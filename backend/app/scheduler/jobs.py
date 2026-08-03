from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from redis.asyncio import Redis

from app.core.logging import get_logger
from app.db.redis import redis_pool
from app.db.session import AsyncSessionLocal
from app.modules.analytics.service import AnalyticsService
from app.modules.calendar.repository import CalendarAccountRepository
from app.modules.calendar.service import CalendarService
from app.modules.email.repository import EmailAccountRepository
from app.modules.email.service import EmailIntegrationService
from app.modules.notifications.service import NotificationService
from app.modules.organizations.repository import OrganizationRepository

logger = get_logger(__name__)

DEFAULT_LOCK_TTL_SECONDS = 300
DAILY_LOCK_TTL_SECONDS = 3600


async def _acquire_lock(redis: Redis, job_name: str, ttl: int) -> bool:
    """Redis-based lock so a scaled-out deployment never double-runs a job.
    Fails open on Redis errors so a Redis blip doesn't silently stop the
    only instance's scheduled work."""
    try:
        acquired = await redis.set(f"scheduler_lock:{job_name}", "1", nx=True, ex=ttl)
        return bool(acquired)
    except Exception:
        logger.warning("scheduler.lock_error", job=job_name)
        return True


async def process_due_notifications() -> None:
    job_name = "process_due_notifications"
    redis = Redis(connection_pool=redis_pool)
    try:
        if not await _acquire_lock(redis, job_name, DEFAULT_LOCK_TTL_SECONDS):
            logger.info("scheduler.skip_locked", job=job_name)
            return
        async with AsyncSessionLocal() as db:
            orgs = await OrganizationRepository(db).list_all_active()
            now = datetime.now(timezone.utc)
            sent_total = 0
            for org in orgs:
                try:
                    result = await NotificationService(db).process_due(
                        tenant_id=org.tenant_id, organization_id=org.id, now=now
                    )
                    await db.commit()
                    sent_total += result.get("sent", 0)
                except Exception:
                    await db.rollback()
                    logger.exception(
                        "scheduler.job_error",
                        job=job_name,
                        tenant_id=str(org.tenant_id),
                        organization_id=str(org.id),
                    )
            logger.info(
                "scheduler.job_done", job=job_name, organizations=len(orgs), sent=sent_total
            )
    finally:
        await redis.aclose()


async def sync_email_accounts() -> None:
    job_name = "sync_email_accounts"
    redis = Redis(connection_pool=redis_pool)
    try:
        if not await _acquire_lock(redis, job_name, DEFAULT_LOCK_TTL_SECONDS):
            logger.info("scheduler.skip_locked", job=job_name)
            return
        async with AsyncSessionLocal() as db:
            accounts = await EmailAccountRepository(db).list_all_connected()
            synced = 0
            for account in accounts:
                try:
                    await EmailIntegrationService(db, redis).sync_messages(account=account)
                    await db.commit()
                    synced += 1
                except Exception:
                    await db.rollback()
                    logger.exception(
                        "scheduler.job_error", job=job_name, account_id=str(account.id)
                    )
            logger.info(
                "scheduler.job_done", job=job_name, accounts=len(accounts), synced=synced
            )
    finally:
        await redis.aclose()


async def sync_calendar_accounts() -> None:
    job_name = "sync_calendar_accounts"
    redis = Redis(connection_pool=redis_pool)
    try:
        if not await _acquire_lock(redis, job_name, DEFAULT_LOCK_TTL_SECONDS):
            logger.info("scheduler.skip_locked", job=job_name)
            return
        async with AsyncSessionLocal() as db:
            accounts = await CalendarAccountRepository(db).list_all_connected()
            synced = 0
            for account in accounts:
                try:
                    await CalendarService(db, redis).sync_events(account=account)
                    await db.commit()
                    synced += 1
                except Exception:
                    await db.rollback()
                    logger.exception(
                        "scheduler.job_error", job=job_name, account_id=str(account.id)
                    )
            logger.info(
                "scheduler.job_done", job=job_name, accounts=len(accounts), synced=synced
            )
    finally:
        await redis.aclose()


async def aggregate_analytics() -> None:
    job_name = "aggregate_analytics"
    redis = Redis(connection_pool=redis_pool)
    try:
        if not await _acquire_lock(redis, job_name, DAILY_LOCK_TTL_SECONDS):
            logger.info("scheduler.skip_locked", job=job_name)
            return
        async with AsyncSessionLocal() as db:
            orgs = await OrganizationRepository(db).list_all_active()
            today = datetime.now(timezone.utc).date()
            aggregated = 0
            for org in orgs:
                try:
                    await AnalyticsService(db).aggregate_for_date(
                        tenant_id=org.tenant_id, organization_id=org.id, date=today
                    )
                    await db.commit()
                    aggregated += 1
                except Exception:
                    await db.rollback()
                    logger.exception(
                        "scheduler.job_error",
                        job=job_name,
                        tenant_id=str(org.tenant_id),
                        organization_id=str(org.id),
                    )
            logger.info(
                "scheduler.job_done", job=job_name, organizations=len(orgs), aggregated=aggregated
            )
    finally:
        await redis.aclose()


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        process_due_notifications,
        IntervalTrigger(minutes=5),
        id="process_due_notifications",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        sync_email_accounts,
        IntervalTrigger(minutes=15),
        id="sync_email_accounts",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        sync_calendar_accounts,
        IntervalTrigger(minutes=30),
        id="sync_calendar_accounts",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        aggregate_analytics,
        IntervalTrigger(hours=24),
        id="aggregate_analytics",
        max_instances=1,
        coalesce=True,
    )
    return scheduler
