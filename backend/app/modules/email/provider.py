import secrets
from datetime import datetime, timedelta, timezone
from typing import Protocol
from urllib.parse import urlencode

import httpx

from app.core.config import settings

GMAIL_METADATA_SCOPE = "https://www.googleapis.com/auth/gmail.metadata"
GOOGLE_BASIC_PROFILE_SCOPE = "openid email"
GOOGLE_AUTHORIZE_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo"
GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"

MICROSOFT_MAIL_SCOPE = "offline_access User.Read Mail.Read"
MICROSOFT_AUTHORIZE_ENDPOINT = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
MICROSOFT_TOKEN_ENDPOINT = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

HTTP_TIMEOUT_SECONDS = 20.0


def _google_redirect_uri() -> str:
    return f"{settings.oauth_redirect_base_url}/api/v1/email/gmail/callback"


def _microsoft_redirect_uri() -> str:
    return f"{settings.oauth_redirect_base_url}/api/v1/email/outlook/callback"


def _google_oauth_scope() -> str:
    return (settings.google_oauth_scopes or f"{GMAIL_METADATA_SCOPE} {GOOGLE_BASIC_PROFILE_SCOPE}").strip()


def _microsoft_oauth_scope() -> str:
    return (settings.microsoft_oauth_scopes or MICROSOFT_MAIL_SCOPE).strip()


class MockGoogleOAuthProvider:
    """Stands in for real Google OAuth (no client_id/secret configured yet)."""

    provider_name = "mock"

    def build_authorize_url(self, *, state: str) -> str:
        params = {
            "client_id": settings.google_client_id or "not-configured",
            "response_type": "code",
            "scope": _google_oauth_scope(),
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
            "scope": _google_oauth_scope(),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        if refresh_token == "[mock-fail]":
            raise RuntimeError("Mock Google OAuth provider failed to refresh token.")

        return {
            "access_token": f"mock-access-refreshed-{secrets.token_urlsafe(16)}",
            "refresh_token": f"mock-refresh-refreshed-{secrets.token_urlsafe(16)}",
            "scope": _google_oauth_scope(),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }


class GoogleOAuthProvider:
    """Real Google OAuth 2.0 authorization-code flow for Gmail readonly access."""

    provider_name = "google"

    def build_authorize_url(self, *, state: str) -> str:
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": _google_redirect_uri(),
            "response_type": "code",
            "scope": _google_oauth_scope(),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{GOOGLE_AUTHORIZE_ENDPOINT}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            response = await client.post(
                GOOGLE_TOKEN_ENDPOINT,
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": _google_redirect_uri(),
                    "grant_type": "authorization_code",
                },
            )
            if response.status_code >= 400:
                raise RuntimeError(f"Google token exchange failed: {response.text}")
            payload = response.json()

            userinfo_response = await client.get(
                GOOGLE_USERINFO_ENDPOINT,
                headers={"Authorization": f"Bearer {payload['access_token']}"},
            )
            userinfo_response.raise_for_status()
            email_address = userinfo_response.json().get("email", "")

        return {
            "email_address": email_address,
            "access_token": payload["access_token"],
            "refresh_token": payload.get("refresh_token", ""),
            "scope": payload.get("scope", _google_oauth_scope()),
            "expires_at": datetime.now(timezone.utc)
            + timedelta(seconds=payload.get("expires_in", 3600)),
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            response = await client.post(
                GOOGLE_TOKEN_ENDPOINT,
                data={
                    "refresh_token": refresh_token,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "grant_type": "refresh_token",
                },
            )
            if response.status_code >= 400:
                raise RuntimeError(f"Google token refresh failed: {response.text}")
            payload = response.json()

        return {
            "access_token": payload["access_token"],
            # Google does not always return a new refresh_token on refresh; keep the old one.
            "refresh_token": payload.get("refresh_token", refresh_token),
            "scope": payload.get("scope", _google_oauth_scope()),
            "expires_at": datetime.now(timezone.utc)
            + timedelta(seconds=payload.get("expires_in", 3600)),
        }


class MockGmailProvider:
    """Stands in for the real Gmail API (no OAuth credentials to call it with yet)."""

    provider_name = "mock"

    async def list_message_metadata(self, *, access_token: str, max_results: int = 10) -> list[dict]:
        now = datetime.now(timezone.utc)
        return [
            {
                "provider_message_id": f"mock-message-{index}",
                "thread_id": f"mock-thread-{index}",
                "subject": f"Mock email subject {index}",
                "from_address": "sender@example.com",
                "snippet": f"This is a mock email snippet number {index}.",
                "body": (
                    f"This is a mock email snippet number {index}.\n\n"
                    f"Full body: following up on our discussion, we would like to proceed "
                    f"with the pricing proposal and schedule a follow-up call to confirm "
                    f"the next steps for message {index}."
                ),
                "received_at": now - timedelta(hours=index),
            }
            for index in range(1, max_results + 1)
        ]


class GmailProvider:
    """Real Gmail API readonly message listing."""

    provider_name = "google"

    async def list_message_metadata(self, *, access_token: str, max_results: int = 10) -> list[dict]:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            list_response = await client.get(
                f"{GMAIL_API_BASE}/messages",
                params={"maxResults": max_results},
                headers=headers,
            )
            list_response.raise_for_status()
            message_ids = [item["id"] for item in list_response.json().get("messages", [])]

            results: list[dict] = []
            for message_id in message_ids:
                detail_response = await client.get(
                    f"{GMAIL_API_BASE}/messages/{message_id}",
                    params={"format": "metadata", "metadataHeaders": ["Subject", "From"]},
                    headers=headers,
                )
                detail_response.raise_for_status()
                detail = detail_response.json()
                message_headers = {
                    header["name"]: header["value"]
                    for header in detail.get("payload", {}).get("headers", [])
                }
                received_at = (
                    datetime.fromtimestamp(int(detail["internalDate"]) / 1000, tz=timezone.utc)
                    if detail.get("internalDate")
                    else datetime.now(timezone.utc)
                )
                results.append(
                    {
                        "provider_message_id": detail["id"],
                        "thread_id": detail.get("threadId", detail["id"]),
                        "subject": message_headers.get("Subject"),
                        "from_address": message_headers.get("From"),
                        "snippet": detail.get("snippet", ""),
                        "body": detail.get("snippet", ""),
                        "received_at": received_at,
                    }
                )
            return results


class MockMicrosoftOAuthProvider:
    """Stands in for real Microsoft identity platform OAuth (no client_id/secret configured yet)."""

    provider_name = "mock"

    def build_authorize_url(self, *, state: str) -> str:
        params = {
            "client_id": settings.microsoft_client_id or "not-configured",
            "response_type": "code",
            "scope": _microsoft_oauth_scope(),
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
            "scope": _microsoft_oauth_scope(),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        if refresh_token == "[mock-fail]":
            raise RuntimeError("Mock Microsoft Graph OAuth provider failed to refresh token.")

        return {
            "access_token": f"mock-graph-access-refreshed-{secrets.token_urlsafe(16)}",
            "refresh_token": f"mock-graph-refresh-refreshed-{secrets.token_urlsafe(16)}",
            "scope": _microsoft_oauth_scope(),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }


class MicrosoftOAuthProvider:
    """Real Microsoft identity platform OAuth 2.0 authorization-code flow for Graph Mail.Read."""

    provider_name = "microsoft"

    def build_authorize_url(self, *, state: str) -> str:
        params = {
            "client_id": settings.microsoft_client_id,
            "redirect_uri": _microsoft_redirect_uri(),
            "response_type": "code",
            "scope": _microsoft_oauth_scope(),
            "response_mode": "query",
            "state": state,
        }
        return f"{MICROSOFT_AUTHORIZE_ENDPOINT}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            response = await client.post(
                MICROSOFT_TOKEN_ENDPOINT,
                data={
                    "code": code,
                    "client_id": settings.microsoft_client_id,
                    "client_secret": settings.microsoft_client_secret,
                    "redirect_uri": _microsoft_redirect_uri(),
                    "grant_type": "authorization_code",
                    "scope": _microsoft_oauth_scope(),
                },
            )
            if response.status_code >= 400:
                raise RuntimeError(f"Microsoft token exchange failed: {response.text}")
            payload = response.json()

            profile_response = await client.get(
                f"{GRAPH_API_BASE}/me",
                headers={"Authorization": f"Bearer {payload['access_token']}"},
            )
            profile_response.raise_for_status()
            profile = profile_response.json()
            email_address = profile.get("mail") or profile.get("userPrincipalName", "")

        return {
            "email_address": email_address,
            "access_token": payload["access_token"],
            "refresh_token": payload.get("refresh_token", ""),
            "scope": payload.get("scope", _microsoft_oauth_scope()),
            "expires_at": datetime.now(timezone.utc)
            + timedelta(seconds=payload.get("expires_in", 3600)),
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            response = await client.post(
                MICROSOFT_TOKEN_ENDPOINT,
                data={
                    "refresh_token": refresh_token,
                    "client_id": settings.microsoft_client_id,
                    "client_secret": settings.microsoft_client_secret,
                    "grant_type": "refresh_token",
                    "scope": _microsoft_oauth_scope(),
                },
            )
            if response.status_code >= 400:
                raise RuntimeError(f"Microsoft token refresh failed: {response.text}")
            payload = response.json()

        return {
            "access_token": payload["access_token"],
            "refresh_token": payload.get("refresh_token", refresh_token),
            "scope": payload.get("scope", _microsoft_oauth_scope()),
            "expires_at": datetime.now(timezone.utc)
            + timedelta(seconds=payload.get("expires_in", 3600)),
        }


class MockOutlookMailProvider:
    """Stands in for the real Microsoft Graph mail API (no OAuth credentials yet)."""

    provider_name = "mock"

    async def list_message_metadata(self, *, access_token: str, max_results: int = 10) -> list[dict]:
        now = datetime.now(timezone.utc)
        return [
            {
                "provider_message_id": f"mock-graph-message-{index}",
                "thread_id": f"mock-graph-conversation-{index}",
                "subject": f"Mock Outlook subject {index}",
                "from_address": "sender@example.com",
                "snippet": f"This is a mock Outlook email snippet number {index}.",
                "body": (
                    f"This is a mock Outlook email snippet number {index}.\n\n"
                    f"Full body: following up on our discussion, we would like to proceed "
                    f"with the pricing proposal and schedule a follow-up call to confirm "
                    f"the next steps for message {index}."
                ),
                "received_at": now - timedelta(hours=index),
            }
            for index in range(1, max_results + 1)
        ]


class OutlookMailProvider:
    """Real Microsoft Graph mail listing."""

    provider_name = "microsoft"

    async def list_message_metadata(self, *, access_token: str, max_results: int = 10) -> list[dict]:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            response = await client.get(
                f"{GRAPH_API_BASE}/me/messages",
                params={
                    "$top": max_results,
                    "$select": "subject,from,bodyPreview,receivedDateTime,conversationId",
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            items = response.json().get("value", [])

        results: list[dict] = []
        for item in items:
            received_at = (
                datetime.fromisoformat(item["receivedDateTime"].replace("Z", "+00:00"))
                if item.get("receivedDateTime")
                else datetime.now(timezone.utc)
            )
            results.append(
                {
                    "provider_message_id": item["id"],
                    "thread_id": item.get("conversationId", item["id"]),
                    "subject": item.get("subject"),
                    "from_address": (item.get("from") or {}).get("emailAddress", {}).get("address"),
                    "snippet": item.get("bodyPreview", ""),
                    "body": item.get("bodyPreview", ""),
                    "received_at": received_at,
                }
            )
        return results


class OAuthProvider(Protocol):
    def build_authorize_url(self, *, state: str) -> str: ...
    async def exchange_code(self, code: str) -> dict: ...
    async def refresh_token(self, refresh_token: str) -> dict: ...


class MailProvider(Protocol):
    async def list_message_metadata(self, *, access_token: str, max_results: int = 10) -> list[dict]: ...


def get_oauth_provider(provider: str) -> OAuthProvider:
    if provider == "gmail":
        if _has_oauth_credentials(settings.google_client_id, settings.google_client_secret):
            return GoogleOAuthProvider()
        if settings.env.lower() in {"production", "prod"}:
            raise RuntimeError(
                "Gmail OAuth bilgileri yapılandırılmamış. GOOGLE_CLIENT_ID ve GOOGLE_CLIENT_SECRET değerlerini backend .env dosyasında tanımlayıp backend'i yeniden başlatın."
            )
        return MockGoogleOAuthProvider()
    if provider == "outlook":
        if _has_oauth_credentials(settings.microsoft_client_id, settings.microsoft_client_secret):
            return MicrosoftOAuthProvider()
        if settings.env.lower() in {"production", "prod"}:
            raise RuntimeError(
                "Outlook OAuth bilgileri yapılandırılmamış. MICROSOFT_CLIENT_ID ve MICROSOFT_CLIENT_SECRET değerlerini backend .env dosyasında tanımlayıp backend'i yeniden başlatın."
            )
        return MockMicrosoftOAuthProvider()
    raise RuntimeError(f"Unsupported email OAuth provider: {provider}")


def get_mail_provider(provider: str) -> MailProvider:
    if provider == "gmail":
        if _has_oauth_credentials(settings.google_client_id, settings.google_client_secret):
            return GmailProvider()
        return MockGmailProvider()
    if provider == "outlook":
        if _has_oauth_credentials(settings.microsoft_client_id, settings.microsoft_client_secret):
            return OutlookMailProvider()
        return MockOutlookMailProvider()
    raise RuntimeError(f"Unsupported email mail provider: {provider}")


def _has_oauth_credentials(client_id: str | None, client_secret: str | None) -> bool:
    invalid_values = {
        "",
        "not-configured",
        "not_configured",
        "changeme",
        "your-client-id",
        "your-client-secret",
        "your-google-client-id",
        "your-google-client-secret",
        "your-microsoft-client-id",
        "your-microsoft-client-secret",
    }
    return (client_id or "").strip().lower() not in invalid_values and (
        client_secret or ""
    ).strip().lower() not in invalid_values
