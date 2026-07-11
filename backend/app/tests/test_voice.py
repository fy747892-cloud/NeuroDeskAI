import base64

from httpx import AsyncClient


async def _register(client: AsyncClient, email: str) -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SuperSecret123", "display_name": "Test User"},
    )
    assert response.status_code == 201
    return response.json()


async def _auth_headers(client: AsyncClient, email: str) -> dict[str, str]:
    tokens = await _register(client, email=email)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def test_voice_command_interprets_task_intent(client: AsyncClient):
    headers = await _auth_headers(client, "voice-task@example.com")

    response = await client.post(
        "/api/v1/voice/commands/interpret",
        headers=headers,
        json={"text": "Yarın acil görev olarak teklif takibini ekle"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["transcript"]["provider"] == "mock"
    assert body["action"]["intent"] == "create_task"
    assert body["action"]["suggested_payload"]["priority"] == "high"
    assert body["action"]["requires_approval"] is True


async def test_voice_command_accepts_mock_base64_audio(client: AsyncClient):
    headers = await _auth_headers(client, "voice-audio@example.com")
    encoded = base64.b64encode("Bugün toplantı planla".encode()).decode()

    response = await client.post(
        "/api/v1/voice/commands/interpret",
        headers=headers,
        json={"audio_base64": encoded},
    )
    assert response.status_code == 200
    assert response.json()["action"]["intent"] == "create_appointment"
