import secrets
from datetime import datetime, timedelta, timezone
from typing import Protocol
from urllib.parse import urlencode

from app.core.config import settings

GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
GOOGLE_AUTHORIZE_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"

MICROSOFT_MAIL_SCOPE = "https://graph.microsoft.com/Mail.Read offline_access"
MICROSOFT_AUTHORIZE_ENDPOINT = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"


class MockGoogleOAuthProvider:
    """Stands in for real Google OAuth (no client_id/secret configured yet)."""

    provider_name = "mock"

    def build_authorize_url(self, *, state: str) -> str:
        params = {
            "client_id": settings.google_client_id or "not-configured",
            "response_type": "code",
            "scope": GMAIL_READONLY_SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{GOOGLE_AUTHORIZE_ENDPOINT}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict:
        if code == "[mock-fail]":
            raise RuntimeError("Mock Google OAuth provider failed to exchange code.")

        return {
            "email_address": "connected-user@gmail.com",
            "access_token": f"mock-access-{secrets.token_urlsafe(16)}",
            "refresh_token": f"mock-refresh-{secrets.token_urlsafe(16)}",
            "scope": GMAIL_READONLY_SCOPE,
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        if refresh_token == "[mock-fail]":
            raise RuntimeError("Mock Google OAuth provider failed to refresh token.")

        return {
            "access_token": f"mock-access-refreshed-{secrets.token_urlsafe(16)}",
            "refresh_token": f"mock-refresh-refreshed-{secrets.token_urlsafe(16)}",
            "scope": GMAIL_READONLY_SCOPE,
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }


class MockGmailProvider:
    """Stands in for the real Gmail API (no OAuth credentials to call it with yet)."""

    provider_name = "mock"

    async def list_message_metadata(self, *, max_results: int = 10) -> list[dict]:
        now = datetime.now(timezone.utc)
        return [
            {
                "provider_message_id": f"mock-message-{index}",
                "thread_id": f"mock-thread-{index}",
                "subject": f"Mock email subject {index}",
                "from_address": "sender@example.com",
                "snippet": f"This is a mock email snippet number {index}.",
                "received_at": now - timedelta(hours=index),
            }
            for index in range(1, max_results + 1)
        ]


class MockMicrosoftOAuthProvider:
    """Stands in for real Microsoft identity platform OAuth (no client_id/secret configured yet)."""

    provider_name = "mock"

    def build_authorize_url(self, *, state: str) -> str:
        params = {
            "client_id": settings.microsoft_client_id or "not-configured",
            "response_type": "code",
            "scope": MICROSOFT_MAIL_SCOPE,
            "response_mode": "query",
            "state": state,
        }
        return f"{MICROSOFT_AUTHORIZE_ENDPOINT}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict:
        if code == "[mock-fail]":
            raise RuntimeError("Mock Microsoft Graph OAuth provider failed to exchange code.")

        return {
            "email_address": "connected-user@outlook.com",
            "access_token": f"mock-graph-access-{secrets.token_urlsafe(16)}",
            "refresh_token": f"mock-graph-refresh-{secrets.token_urlsafe(16)}",
            "scope": MICROSOFT_MAIL_SCOPE,
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        if refresh_token == "[mock-fail]":
            raise RuntimeError("Mock Microsoft Graph OAuth provider failed to refresh token.")

        return {
            "access_token": f"mock-graph-access-refreshed-{secrets.token_urlsafe(16)}",
            "refresh_token": f"mock-graph-refresh-refreshed-{secrets.token_urlsafe(16)}",
            "scope": MICROSOFT_MAIL_SCOPE,
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }


class MockOutlookMailProvider:
    """Stands in for the real Microsoft Graph mail API (no OAuth credentials yet)."""

    provider_name = "mock"

    async def list_message_metadata(self, *, max_results: int = 10) -> list[dict]:
        now = datetime.now(timezone.utc)
        return [
            {
                "provider_message_id": f"mock-graph-message-{index}",
                "thread_id": f"mock-graph-conversation-{index}",
                "subject": f"Mock Outlook subject {index}",
                "from_address": "sender@example.com",
                "snippet": f"This is a mock Outlook email snippet number {index}.",
                "received_at": now - timedelta(hours=index),
            }
            for index in range(1, max_results + 1)
        ]


class OAuthProvider(Protocol):
    def build_authorize_url(self, *, state: str) -> str: ...
    async def exchange_code(self, code: str) -> dict: ...
    async def refresh_token(self, refresh_token: str) -> dict: ...


class MailProvider(Protocol):
    async def list_message_metadata(self, *, max_results: int = 10) -> list[dict]: ...


OAUTH_PROVIDERS: dict[str, type[OAuthProvider]] = {
    "gmail": MockGoogleOAuthProvider,
    "outlook": MockMicrosoftOAuthProvider,
}

MAIL_PROVIDERS: dict[str, type[MailProvider]] = {
    "gmail": MockGmailProvider,
    "outlook": MockOutlookMailProvider,
}
