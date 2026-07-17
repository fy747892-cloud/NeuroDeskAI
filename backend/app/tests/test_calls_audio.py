from httpx import AsyncClient


async def _auth_headers(client: AsyncClient, email: str) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SuperSecret123", "display_name": "Test User"},
    )
    assert response.status_code == 201
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def test_create_call_from_audio_transcribes_and_is_analyzable(client: AsyncClient):
    headers = await _auth_headers(client, "audio-call@example.com")

    response = await client.post(
        "/api/v1/calls/audio",
        headers=headers,
        data={
            "title": "Speakerphone call",
            "participant_names": "Alice, Bob",
            "call_direction": "outbound",
            "phone_number": "+905551112233",
            "language": "tr",
        },
        files={"audio": ("recording.m4a", b"fake-audio-bytes", "audio/mp4")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["transcription"]["transcript_text"].startswith(
        "[mock transcript for recording.m4a"
    )
    assert body["call"]["call_direction"] == "outbound"
    assert body["call"]["phone_number"] == "+905551112233"

    conversation_id = body["conversation"]["id"]
    analysis_response = await client.post(
        f"/api/v1/ai/analysis/conversations/{conversation_id}",
        headers=headers,
    )
    assert analysis_response.status_code == 201
    assert analysis_response.json()["status"] == "completed"


async def test_create_call_from_audio_rejects_empty_file(client: AsyncClient):
    headers = await _auth_headers(client, "audio-call-empty@example.com")

    response = await client.post(
        "/api/v1/calls/audio",
        headers=headers,
        data={"title": "Empty call"},
        files={"audio": ("recording.m4a", b"", "audio/mp4")},
    )

    assert response.status_code == 422
