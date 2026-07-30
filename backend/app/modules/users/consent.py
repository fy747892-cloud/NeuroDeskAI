from app.modules.users.models import User

DEFAULT_CONSENT = {
    "ai_processing": True,
    "contact_memory": True,
    "operational_reminders": True,
}


def get_consent(user: User) -> dict[str, bool]:
    metadata = user.user_metadata or {}
    stored = metadata.get("consent") if isinstance(metadata, dict) else None
    consent = dict(DEFAULT_CONSENT)
    if isinstance(stored, dict):
        consent.update({key: bool(value) for key, value in stored.items() if key in DEFAULT_CONSENT})
    return consent
