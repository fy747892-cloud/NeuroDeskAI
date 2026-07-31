import base64

from httpx import AsyncClient

# A valid 1x1 transparent PNG, used as minimal real image bytes for upload tests.
TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


async def _auth_headers(client: AsyncClient, email: str) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SuperSecret123", "display_name": "Test User"},
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def test_upload_avatar_sets_profile_url(client: AsyncClient):
    headers = await _auth_headers(client, "avatar-upload@example.com")

    response = await client.post(
        "/api/v1/users/me/avatar",
        headers=headers,
        files={"file": ("avatar.png", TINY_PNG, "image/png")},
    )
    assert response.status_code == 200
    avatar_url = response.json()["profile"]["avatar_url"]
    assert avatar_url is not None
    assert "/avatar" in avatar_url

    me_response = await client.get("/api/v1/users/me", headers=headers)
    assert me_response.json()["profile"]["avatar_url"] == avatar_url


async def test_uploaded_avatar_is_publicly_servable(client: AsyncClient):
    headers = await _auth_headers(client, "avatar-serve@example.com")
    upload_response = await client.post(
        "/api/v1/users/me/avatar",
        headers=headers,
        files={"file": ("avatar.png", TINY_PNG, "image/png")},
    )
    user_id = upload_response.json()["id"]

    avatar_response = await client.get(f"/api/v1/users/{user_id}/avatar")
    assert avatar_response.status_code == 200
    assert avatar_response.headers["content-type"] == "image/png"
    assert avatar_response.content == TINY_PNG


async def test_avatar_upload_rejects_non_image_mime_type(client: AsyncClient):
    headers = await _auth_headers(client, "avatar-bad-type@example.com")
    response = await client.post(
        "/api/v1/users/me/avatar",
        headers=headers,
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 422


async def test_avatar_upload_rejects_oversized_file(client: AsyncClient):
    headers = await _auth_headers(client, "avatar-too-big@example.com")
    oversized = b"\x00" * (2 * 1024 * 1024 + 1)
    response = await client.post(
        "/api/v1/users/me/avatar",
        headers=headers,
        files={"file": ("avatar.png", oversized, "image/png")},
    )
    assert response.status_code == 422


async def test_reuploading_avatar_replaces_previous_image(client: AsyncClient):
    headers = await _auth_headers(client, "avatar-replace@example.com")
    first_upload = await client.post(
        "/api/v1/users/me/avatar",
        headers=headers,
        files={"file": ("avatar.png", TINY_PNG, "image/png")},
    )
    user_id = first_upload.json()["id"]
    first_avatar_url = first_upload.json()["profile"]["avatar_url"]

    other_png = TINY_PNG + b"\x00"
    second_upload = await client.post(
        "/api/v1/users/me/avatar",
        headers=headers,
        files={"file": ("avatar2.png", other_png, "image/png")},
    )
    assert second_upload.json()["profile"]["avatar_url"] == first_avatar_url

    avatar_response = await client.get(f"/api/v1/users/{user_id}/avatar")
    assert avatar_response.content == other_png


async def test_delete_avatar_clears_it(client: AsyncClient):
    headers = await _auth_headers(client, "avatar-delete@example.com")
    upload_response = await client.post(
        "/api/v1/users/me/avatar",
        headers=headers,
        files={"file": ("avatar.png", TINY_PNG, "image/png")},
    )
    user_id = upload_response.json()["id"]

    delete_response = await client.delete("/api/v1/users/me/avatar", headers=headers)
    assert delete_response.status_code == 204

    me_response = await client.get("/api/v1/users/me", headers=headers)
    assert me_response.json()["profile"]["avatar_url"] is None

    avatar_response = await client.get(f"/api/v1/users/{user_id}/avatar")
    assert avatar_response.status_code == 404


async def test_avatar_not_found_for_user_without_one(client: AsyncClient):
    headers = await _auth_headers(client, "avatar-none@example.com")
    me_response = await client.get("/api/v1/users/me", headers=headers)
    user_id = me_response.json()["id"]

    avatar_response = await client.get(f"/api/v1/users/{user_id}/avatar")
    assert avatar_response.status_code == 404
