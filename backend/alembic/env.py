import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.core.config import settings
from app.db.base import Base
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
from app.modules.calendar.models import CalendarAccount  # noqa: F401
from app.modules.contacts.models import Contact, ContactNote, ContactTimelineEvent  # noqa: F401
from app.modules.conversations.models import (  # noqa: F401
    Call,
    CallTranscription,
    Conversation,
    ConversationParticipant,
)
from app.modules.email.models import EmailAccount, EmailMessageMetadata, EmailToken  # noqa: F401
from app.modules.files.models import DocumentAnalysisResult, DocumentText, File  # noqa: F401
from app.modules.notifications.models import Notification  # noqa: F401
from app.modules.organizations.models import Organization, OrganizationMember, Tenant  # noqa: F401
from app.modules.search.models import Embedding  # noqa: F401
from app.modules.tasks.models import Task  # noqa: F401
from app.modules.users.models import User, UserProfile  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
