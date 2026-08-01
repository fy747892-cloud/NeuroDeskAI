import secrets
from datetime import datetime, timedelta, timezone
from typing import Protocol
from urllib.parse import urlencode

import httpx

from app.core.config import settings

GOOGLE_CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
GOOGLE_BASIC_PROFILE_SCOPE = "openid email"
GOOGLE_AUTHORIZE_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"

HTTP_TIMEOUT_SECONDS = 20.0


def _google_redirect_uri() -> str:
    return f"{settings.oauth_redirect_base_url}/api/v1/calendar/google/callback"


def _google_calendar_oauth_scope() -> str:
    return (settings.google_calendar_oauth_scopes or f"{GOOGLE_CALENDAR_SCOPE} {GOOGLE_BASIC_PROFILE_SCOPE}").strip()


class MockGoogleCalendarOAuthProvider:
    """Stands in for real Google OAuth (no client_id/secret configured yet)."""

    provider_name = "mock"

    def build_authorize_url(self, *, state: str) -> str:
        params = {
            "client_id": settings.google_client_id or "not-configured",
            "response_type": "code",
            "scope": _google_calendar_oauth_scope(),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{GOOGLE_AUTHORIZE_ENDPOINT}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict:
        if code == "[mock-fail]":
            raise RuntimeError("Mock Google Calendar OAuth provider failed to exchange code.")

        return {
            "email_address": "connected-user@gmail.com",
            "access_token": f"mock-access-{secrets.token_urlsafe(16)}",
            "refresh_token": f"mock-refresh-{secrets.token_urlsafe(16)}",
            "scope": _google_calendar_oauth_scope(),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        if refresh_token == "[mock-fail]":
            raise RuntimeError("Mock Google Calendar OAuth provider failed to refresh token.")

        return {
            "access_token": f"mock-access-refreshed-{secrets.token_urlsafe(16)}",
            "refresh_token": f"mock-refresh-refreshed-{secrets.token_urlsafe(16)}",
            "scope": _google_calendar_oauth_scope(),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }


class GoogleCalendarOAuthProvider:
    """Real Google OAuth 2.0 authorization-code flow for Calendar readonly access."""

    provider_name = "google"

    def build_authorize_url(self, *, state: str) -> str:
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": _google_redirect_uri(),
            "response_type": "code",
            "scope": _google_calendar_oauth_scope(),
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
            "scope": payload.get("scope", _google_calendar_oauth_scope()),
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
            "scope": payload.get("scope", _google_calendar_oauth_scope()),
            "expires_at": datetime.now(timezone.utc)
            + timedelta(seconds=payload.get("expires_in", 3600)),
        }


class MockCalendarEventsProvider:
    """Stands in for the real Google Calendar API (no OAuth credentials to call it with yet)."""

    provider_name = "mock"

    async def list_events(
        self, *, access_token: str, time_min: datetime, max_results: int = 20
    ) -> list[dict]:
        now = datetime.now(timezone.utc)
        return [
            {
                "external_event_id": f"mock-event-{index}",
                "title": f"Mock calendar event {index}",
                "description": f"This is a mock Google Calendar event number {index}.",
                "location": None,
                "start_at": now + timedelta(days=index, hours=1),
                "end_at": now + timedelta(days=index, hours=2),
                "status": "confirmed",
            }
            for index in range(1, min(max_results, 5) + 1)
        ]


class GoogleCalendarEventsProvider:
    """Real Google Calendar API readonly event listing."""

    provider_name = "google"

    async def list_events(
        self, *, access_token: str, time_min: datetime, max_results: int = 20
    ) -> list[dict]:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            response = await client.get(
                f"{GOOGLE_CALENDAR_API_BASE}/calendars/primary/events",
                params={
                    "timeMin": time_min.isoformat(),
                    "maxResults": max_results,
                    "singleEvents": "true",
                    "orderBy": "startTime",
                },
                headers=headers,
            )
            response.raise_for_status()
            items = response.json().get("items", [])

        results: list[dict] = []
        for item in items:
            start_at = _parse_event_datetime(item.get("start"))
            end_at = _parse_event_datetime(item.get("end")) or start_at
            if start_at is None:
                continue
            results.append(
                {
                    "external_event_id": item["id"],
                    "title": item.get("summary") or "",
                    "description": item.get("description"),
                    "location": item.get("location"),
                    "start_at": start_at,
                    "end_at": end_at,
                    "status": item.get("status", "confirmed"),
                }
            )
        return results


def _parse_event_datetime(value: dict | None) -> datetime | None:
    if not value:
        return None
    if value.get("dateTime"):
        return datetime.fromisoformat(value["dateTime"].replace("Z", "+00:00"))
    if value.get("date"):
        # All-day event: Google gives a bare date, treat as midnight UTC.
        return datetime.fromisoformat(value["date"]).replace(tzinfo=timezone.utc)
    return None


class CalendarOAuthProvider(Protocol):
    def build_authorize_url(self, *, state: str) -> str: ...
    async def exchange_code(self, code: str) -> dict: ...
    async def refresh_token(self, refresh_token: str) -> dict: ...


class CalendarEventsProvider(Protocol):
    async def list_events(
        self, *, access_token: str, time_min: datetime, max_results: int = 20
    ) -> list[dict]: ...


def get_calendar_oauth_provider() -> CalendarOAuthProvider:
    if _has_oauth_credentials(settings.google_client_id, settings.google_client_secret):
        return GoogleCalendarOAuthProvider()
    if settings.env.lower() in {"production", "prod"}:
        raise RuntimeError(
            "Google Calendar OAuth bilgileri yapılandırılmamış. GOOGLE_CLIENT_ID ve "
            "GOOGLE_CLIENT_SECRET değerlerini backend .env dosyasında tanımlayıp backend'i "
            "yeniden başlatın."
        )
    return MockGoogleCalendarOAuthProvider()


def get_calendar_events_provider() -> CalendarEventsProvider:
    if _has_oauth_credentials(settings.google_client_id, settings.google_client_secret):
        return GoogleCalendarEventsProvider()
    return MockCalendarEventsProvider()


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
    }
    return (client_id or "").strip().lower() not in invalid_values and (
        client_secret or ""
    ).strip().lower() not in invalid_values
