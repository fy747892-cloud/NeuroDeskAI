from fastapi import APIRouter

from app.api.v1.ai import approval_router, router as ai_router
from app.api.v1.ai_chat import router as ai_chat_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.appointments import router as appointments_router
from app.api.v1.audit_logs import router as audit_logs_router
from app.api.v1.auth import router as auth_router
from app.api.v1.billing import router as billing_router
from app.api.v1.calendar import router as calendar_router
from app.api.v1.calls import router as calls_router
from app.api.v1.client_errors import router as client_errors_router
from app.api.v1.contacts import router as contacts_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.deals import router as deals_router
from app.api.v1.email import router as email_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.files import router as files_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.organizations import router as organizations_router
from app.api.v1.priority import router as priority_router
from app.api.v1.search import router as search_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.users import router as users_router
from app.api.v1.voice import router as voice_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(organizations_router)
api_router.include_router(audit_logs_router)
api_router.include_router(conversations_router)
api_router.include_router(calls_router)
api_router.include_router(ai_router)
api_router.include_router(approval_router)
api_router.include_router(tasks_router)
api_router.include_router(appointments_router)
api_router.include_router(priority_router)
api_router.include_router(calendar_router)
api_router.include_router(notifications_router)
api_router.include_router(dashboard_router)
api_router.include_router(contacts_router)
api_router.include_router(ai_chat_router)
api_router.include_router(search_router)
api_router.include_router(voice_router)
api_router.include_router(email_router)
api_router.include_router(files_router)
api_router.include_router(analytics_router)
api_router.include_router(billing_router)
api_router.include_router(deals_router)
api_router.include_router(client_errors_router)
api_router.include_router(feedback_router)
