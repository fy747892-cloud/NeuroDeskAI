import secrets
from urllib.parse import urlencode

import httpx

from app.core.config import settings

GOOGLE_AUTHORIZE_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo"
LOGIN_SCOPE = "openid email profile"
HTTP_TIMEOUT_SECONDS = 20.0


def _redirect_uri() -> str:
    return f"{settings.oauth_redirect_base_url}/api/v1/auth/google/callback"


def _has_credentials() -> bool:
    invalid_values = {"", "not-configured", "not_configured", "changeme"}
    return (
        settings.google_client_id not in invalid_values
        and settings.google_client_secret not in invalid_values
    )


class MockGoogleLoginProvider:
    """Stands in for real Google Sign-In when no client credentials are configured."""

    provider_name = "mock"

    def build_authorize_url(self, *, state: str) -> str:
        params = {
            "client_id": settings.google_client_id or "not-configured",
            "response_type": "code",
            "scope": LOGIN_SCOPE,
            "state": state,
        }
        return f"{GOOGLE_AUTHORIZE_ENDPOINT}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict:
        if code == "[mock-fail]":
            raise RuntimeError("Mock Google login provider failed to exchange code.")
        return {
            "email": f"mock-google-user-{secrets.token_hex(4)}@example.com",
            "email_verified": True,
            "name": "Mock Google User",
        }


class GoogleLoginProvider:
    """Real Google OAuth 2.0 authorization-code flow for Sign in with Google."""

    provider_name = "google"

    def build_authorize_url(self, *, state: str) -> str:
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": _redirect_uri(),
            "response_type": "code",
            "scope": LOGIN_SCOPE,
            "state": state,
        }
        return f"{GOOGLE_AUTHORIZE_ENDPOINT}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            token_response = await client.post(
                GOOGLE_TOKEN_ENDPOINT,
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": _redirect_uri(),
                    "grant_type": "authorization_code",
                },
            )
            if token_response.status_code >= 400:
                raise RuntimeError(f"Google token exchange failed: {token_response.text}")
            access_token = token_response.json()["access_token"]

            userinfo_response = await client.get(
                GOOGLE_USERINFO_ENDPOINT,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            userinfo_response.raise_for_status()
            payload = userinfo_response.json()

        return {
            "email": payload.get("email", ""),
            "email_verified": bool(payload.get("verified_email", False)),
            "name": payload.get("name", ""),
        }


def get_google_login_provider():
    if _has_credentials():
        return GoogleLoginProvider()
    if settings.env.lower() in {"production", "prod"}:
        raise RuntimeError(
            "Google ile giriş yapılandırılmamış. GOOGLE_CLIENT_ID ve GOOGLE_CLIENT_SECRET "
            "değerlerini backend .env dosyasında tanımlayıp backend'i yeniden başlatın."
        )
    return MockGoogleLoginProvider()
