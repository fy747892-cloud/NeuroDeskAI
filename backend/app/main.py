from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.db.redis import redis_pool
from app.db.storage import ensure_bucket
from app.scheduler.jobs import create_scheduler

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.env)
    await ensure_bucket()

    scheduler = None
    if settings.scheduler_enabled:
        scheduler = create_scheduler()
        scheduler.start()
        logger.info("scheduler.started")

    yield

    if scheduler is not None:
        scheduler.shutdown(wait=False)
        logger.info("scheduler.stopped")
    await redis_pool.disconnect()


app = FastAPI(title="NeuroDesk AI Backend", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
