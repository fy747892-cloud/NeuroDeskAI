import os

# Force mock providers for the test session regardless of the developer's local .env —
# tests must stay free, fast, and isolated from real external services (OpenAI billing,
# outbound SMTP email). Set before any app import triggers Settings() to load.
os.environ["LLM_PROVIDER"] = "mock"
os.environ["EMAIL_PROVIDER"] = "mock"
os.environ["DIARIZATION_PROVIDER"] = "disabled"

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.redis import get_redis
from app.db.session import get_db
from app.main import app
from app.modules.ai.models import (  # noqa: F401
    AIActionApproval,
    AIAnalysisJob,
    AIAnalysisResult,
    AIPromptVersion,
)
from app.modules.ai_chat.models import ChatMessage, ChatSession  # noqa: F401
from app.modules.analytics.models import (  # noqa: F401
    AICostLog,
    AnalyticsAIMetric,
    AnalyticsAppointmentMetric,
    AnalyticsCallMetric,
    AnalyticsDailyUserStat,
    AnalyticsTaskMetric,
)
from app.modules.appointments.models import Appointment  # noqa: F401
from app.modules.audit.models import AuditLog  # noqa: F401
from app.modules.auth.models import RefreshToken, UserSession  # noqa: F401
from app.modules.billing.models import Plan, Subscription, UsageQuota, UsageRecord  # noqa: F401
from app.modules.calendar.models import CalendarAccount, CalendarToken  # noqa: F401
from app.modules.contacts.models import Contact, ContactNote, ContactTimelineEvent  # noqa: F401
from app.modules.conversations.models import (  # noqa: F401
    Call,
    CallTranscription,
    Conversation,
    ConversationParticipant,
)
from app.modules.deals.models import Deal  # noqa: F401
from app.modules.email.models import EmailAccount, EmailMessageMetadata, EmailToken  # noqa: F401
from app.modules.files.models import DocumentAnalysisResult, DocumentText, File  # noqa: F401
from app.modules.notifications.models import Notification  # noqa: F401
from app.modules.observability.models import ClientErrorReport  # noqa: F401
from app.modules.feedback.models import Feedback  # noqa: F401
from app.modules.organizations.models import Organization, OrganizationMember, Tenant  # noqa: F401
from app.modules.search.models import Embedding  # noqa: F401
from app.modules.tasks.models import Task  # noqa: F401
from app.modules.users.models import User, UserProfile  # noqa: F401
from app.modules.whatsapp.models import WhatsAppMessage  # noqa: F401

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://neurodesk:neurodesk@localhost:5432/neurodesk_test",
)
TEST_REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/15")

test_engine = create_async_engine(TEST_DATABASE_URL)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _create_schema():
    async with test_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session():
    async with test_engine.connect() as connection:
        trans = await connection.begin()
        session_factory = async_sessionmaker(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()


@pytest_asyncio.fixture
async def redis_client():
    client = Redis.from_url(TEST_REDIS_URL)
    await client.flushdb()
    try:
        yield client
    finally:
        await client.flushdb()
        await client.aclose()


@pytest_asyncio.fixture
async def client(db_session, redis_client):
    async def _get_db_override():
        yield db_session

    async def _get_redis_override():
        yield redis_client

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_redis] = _get_redis_override

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
