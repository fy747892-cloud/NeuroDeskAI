from enum import StrEnum

from app.core.errors import ForbiddenError


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Permission(StrEnum):
    USERS_READ = "users.read"
    USERS_UPDATE_SELF = "users.update_self"
    ORGANIZATIONS_READ = "organizations.read"
    ORGANIZATIONS_MANAGE = "organizations.manage"
    ROLES_MANAGE = "roles.manage"
    AUDIT_READ = "audit.read"
    CONVERSATIONS_READ = "conversations.read"
    CONVERSATIONS_CREATE = "conversations.create"
    CONVERSATIONS_MANAGE = "conversations.manage"
    AI_ANALYZE = "ai.analyze"
    AI_READ = "ai.read"
    TASKS_READ = "tasks.read"
    TASKS_MANAGE = "tasks.manage"
    APPOINTMENTS_READ = "appointments.read"
    APPOINTMENTS_MANAGE = "appointments.manage"
    CALENDAR_READ = "calendar.read"
    CALENDAR_CONNECT = "calendar.connect"
    NOTIFICATIONS_READ = "notifications.read"
    NOTIFICATIONS_MANAGE = "notifications.manage"
    DASHBOARD_READ = "dashboard.read"
    CONTACTS_READ = "contacts.read"
    CONTACTS_MANAGE = "contacts.manage"
    AI_CHAT_READ = "ai_chat.read"
    AI_CHAT_USE = "ai_chat.use"
    SEARCH_USE = "search.use"
    SEARCH_MANAGE = "search.manage"
    EMAIL_READ = "email.read"
    EMAIL_CONNECT = "email.connect"
    FILES_READ = "files.read"
    FILES_MANAGE = "files.manage"
    ANALYTICS_READ = "analytics.read"
    ANALYTICS_MANAGE = "analytics.manage"
    BILLING_READ = "billing.read"
    BILLING_MANAGE = "billing.manage"
    DEALS_READ = "deals.read"
    DEALS_MANAGE = "deals.manage"
    WHATSAPP_READ = "whatsapp.read"
    WHATSAPP_MANAGE = "whatsapp.manage"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.OWNER: {
        Permission.USERS_READ,
        Permission.USERS_UPDATE_SELF,
        Permission.ORGANIZATIONS_READ,
        Permission.ORGANIZATIONS_MANAGE,
        Permission.ROLES_MANAGE,
        Permission.AUDIT_READ,
        Permission.CONVERSATIONS_READ,
        Permission.CONVERSATIONS_CREATE,
        Permission.CONVERSATIONS_MANAGE,
        Permission.AI_ANALYZE,
        Permission.AI_READ,
        Permission.TASKS_READ,
        Permission.TASKS_MANAGE,
        Permission.APPOINTMENTS_READ,
        Permission.APPOINTMENTS_MANAGE,
        Permission.CALENDAR_READ,
        Permission.CALENDAR_CONNECT,
        Permission.NOTIFICATIONS_READ,
        Permission.NOTIFICATIONS_MANAGE,
        Permission.DASHBOARD_READ,
        Permission.CONTACTS_READ,
        Permission.CONTACTS_MANAGE,
        Permission.AI_CHAT_READ,
        Permission.AI_CHAT_USE,
        Permission.SEARCH_USE,
        Permission.SEARCH_MANAGE,
        Permission.EMAIL_READ,
        Permission.EMAIL_CONNECT,
        Permission.FILES_READ,
        Permission.FILES_MANAGE,
        Permission.ANALYTICS_READ,
        Permission.ANALYTICS_MANAGE,
        Permission.BILLING_READ,
        Permission.BILLING_MANAGE,
        Permission.DEALS_READ,
        Permission.DEALS_MANAGE,
        Permission.WHATSAPP_READ,
        Permission.WHATSAPP_MANAGE,
    },
    Role.ADMIN: {
        Permission.USERS_READ,
        Permission.USERS_UPDATE_SELF,
        Permission.ORGANIZATIONS_READ,
        Permission.ORGANIZATIONS_MANAGE,
        Permission.AUDIT_READ,
        Permission.CONVERSATIONS_READ,
        Permission.CONVERSATIONS_CREATE,
        Permission.CONVERSATIONS_MANAGE,
        Permission.AI_ANALYZE,
        Permission.AI_READ,
        Permission.TASKS_READ,
        Permission.TASKS_MANAGE,
        Permission.APPOINTMENTS_READ,
        Permission.APPOINTMENTS_MANAGE,
        Permission.CALENDAR_READ,
        Permission.CALENDAR_CONNECT,
        Permission.NOTIFICATIONS_READ,
        Permission.NOTIFICATIONS_MANAGE,
        Permission.DASHBOARD_READ,
        Permission.CONTACTS_READ,
        Permission.CONTACTS_MANAGE,
        Permission.AI_CHAT_READ,
        Permission.AI_CHAT_USE,
        Permission.SEARCH_USE,
        Permission.SEARCH_MANAGE,
        Permission.EMAIL_READ,
        Permission.EMAIL_CONNECT,
        Permission.FILES_READ,
        Permission.FILES_MANAGE,
        Permission.ANALYTICS_READ,
        Permission.ANALYTICS_MANAGE,
        Permission.BILLING_READ,
        Permission.BILLING_MANAGE,
        Permission.DEALS_READ,
        Permission.DEALS_MANAGE,
        Permission.WHATSAPP_READ,
        Permission.WHATSAPP_MANAGE,
    },
    Role.MEMBER: {
        Permission.USERS_READ,
        Permission.USERS_UPDATE_SELF,
        Permission.ORGANIZATIONS_READ,
        Permission.CONVERSATIONS_READ,
        Permission.CONVERSATIONS_CREATE,
        Permission.CONVERSATIONS_MANAGE,
        Permission.AI_ANALYZE,
        Permission.AI_READ,
        Permission.TASKS_READ,
        Permission.TASKS_MANAGE,
        Permission.APPOINTMENTS_READ,
        Permission.APPOINTMENTS_MANAGE,
        Permission.CALENDAR_READ,
        Permission.CALENDAR_CONNECT,
        Permission.NOTIFICATIONS_READ,
        Permission.DASHBOARD_READ,
        Permission.CONTACTS_READ,
        Permission.CONTACTS_MANAGE,
        Permission.AI_CHAT_READ,
        Permission.AI_CHAT_USE,
        Permission.SEARCH_USE,
        Permission.EMAIL_READ,
        Permission.EMAIL_CONNECT,
        Permission.FILES_READ,
        Permission.FILES_MANAGE,
        Permission.ANALYTICS_READ,
        Permission.BILLING_READ,
        Permission.DEALS_READ,
        Permission.DEALS_MANAGE,
        Permission.WHATSAPP_READ,
        Permission.WHATSAPP_MANAGE,
    },
    Role.VIEWER: {
        Permission.USERS_READ,
        Permission.ORGANIZATIONS_READ,
        Permission.CONVERSATIONS_READ,
        Permission.AI_READ,
        Permission.TASKS_READ,
        Permission.APPOINTMENTS_READ,
        Permission.CALENDAR_READ,
        Permission.NOTIFICATIONS_READ,
        Permission.DASHBOARD_READ,
        Permission.CONTACTS_READ,
        Permission.AI_CHAT_READ,
        Permission.EMAIL_READ,
        Permission.FILES_READ,
        Permission.ANALYTICS_READ,
        Permission.BILLING_READ,
        Permission.DEALS_READ,
        Permission.WHATSAPP_READ,
    },
}


def ensure_permission(role: str, permission: Permission) -> None:
    try:
        normalized_role = Role(role)
    except ValueError as exc:
        raise ForbiddenError("This role is not recognized.") from exc

    if permission not in ROLE_PERMISSIONS[normalized_role]:
        raise ForbiddenError("You do not have permission to perform this action.")
