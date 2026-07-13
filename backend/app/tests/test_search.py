from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.organizations.models import OrganizationMember


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


async def _create_task(
    client: AsyncClient, headers: dict[str, str], title: str, description: str | None = None
) -> dict:
    body: dict = {"title": title}
    if description is not None:
        body["description"] = description
    response = await client.post("/api/v1/tasks", headers=headers, json=body)
    assert response.status_code == 201
    return response.json()


async def _connect_gmail_and_sync(client: AsyncClient, headers: dict[str, str]) -> dict:
    start = await client.post("/api/v1/email/gmail/connect", headers=headers)
    assert start.status_code == 200
    callback = await client.get(
        "/api/v1/email/gmail/callback",
        params={"code": "mock-code", "state": start.json()["state"]},
    )
    assert callback.status_code == 200
    account = callback.json()
    sync_response = await client.post(
        f"/api/v1/email/accounts/{account['id']}/sync", headers=headers
    )
    assert sync_response.status_code == 200
    return account


async def _reindex(client: AsyncClient, headers: dict[str, str]) -> dict:
    response = await client.post("/api/v1/search/reindex", headers=headers)
    assert response.status_code == 200
    return response.json()


async def _search(client: AsyncClient, headers: dict[str, str], query: str, limit: int = 10) -> list:
    response = await client.post(
        "/api/v1/search/semantic", headers=headers, json={"query": query, "limit": limit}
    )
    assert response.status_code == 200
    return response.json()


async def test_reindex_creates_skips_unchanged_and_updates(client: AsyncClient):
    headers = await _auth_headers(client, "search-reindex@example.com")
    task = await _create_task(client, headers, "Reindex demo task", "original description")

    first = await _reindex(client, headers)
    assert first["created"] == 1
    assert first["processed"] == 1

    second = await _reindex(client, headers)
    assert second["skipped"] == 1
    assert second["created"] == 0
    assert second["updated"] == 0

    update_response = await client.patch(
        f"/api/v1/tasks/{task['id']}", headers=headers, json={"description": "changed description"}
    )
    assert update_response.status_code == 200

    third = await _reindex(client, headers)
    assert third["updated"] == 1
    assert third["skipped"] == 0
    assert third["created"] == 0


async def test_semantic_search_relevance_smoke(client: AsyncClient):
    headers = await _auth_headers(client, "search-relevance@example.com")
    task_a = await _create_task(client, headers, "Falcon proposal pricing", "pricing details for Falcon")
    task_b = await _create_task(
        client, headers, "Falcon proposal follow-up", "follow up with Falcon client"
    )
    await _create_task(client, headers, "Unrelated grocery list", "milk eggs bread")

    await _reindex(client, headers)
    results = await _search(client, headers, "Falcon proposal")

    top_ids = {r["source_id"] for r in results[:2]}
    assert top_ids == {task_a["id"], task_b["id"]}

    scores_by_id = {r["source_id"]: r["score"] for r in results}
    assert scores_by_id[task_a["id"]] > 0
    assert scores_by_id[task_b["id"]] > 0


async def test_semantic_search_is_tenant_scoped_no_retrieval_leak(client: AsyncClient):
    first_headers = await _auth_headers(client, "search-tenant-one@example.com")
    second_headers = await _auth_headers(client, "search-tenant-two@example.com")

    first_task = await _create_task(client, first_headers, "SharedKeyword999 alpha task")
    await _create_task(client, second_headers, "SharedKeyword999 beta task")

    await _reindex(client, first_headers)
    await _reindex(client, second_headers)

    results = await _search(client, first_headers, "SharedKeyword999")
    source_ids = {r["source_id"] for r in results}
    assert source_ids == {first_task["id"]}


async def test_viewer_cannot_use_semantic_search(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth_headers(client, "search-viewer@example.com")
    me_response = await client.get("/api/v1/users/me", headers=headers)
    user_id = me_response.json()["id"]

    await db_session.execute(
        update(OrganizationMember)
        .where(OrganizationMember.user_id == user_id)
        .values(role="viewer")
    )
    await db_session.flush()

    response = await client.post(
        "/api/v1/search/semantic", headers=headers, json={"query": "anything"}
    )
    assert response.status_code == 403


async def test_reindex_and_search_cover_email_message_bodies(client: AsyncClient):
    headers = await _auth_headers(client, "search-email@example.com")
    account = await _connect_gmail_and_sync(client, headers)

    messages_response = await client.get(
        f"/api/v1/email/accounts/{account['id']}/messages", headers=headers
    )
    assert messages_response.status_code == 200
    message_count = len(messages_response.json())
    assert message_count > 0

    summary = await _reindex(client, headers)
    assert summary["processed"] >= message_count
    assert summary["created"] >= message_count

    results = await _search(client, headers, "pricing proposal follow-up call")
    email_results = [r for r in results if r["source_type"] == "email_message"]
    assert email_results
    assert email_results[0]["title"].startswith("Mock email subject")


async def test_member_can_search_but_cannot_reindex(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth_headers(client, "search-member@example.com")
    me_response = await client.get("/api/v1/users/me", headers=headers)
    user_id = me_response.json()["id"]

    await db_session.execute(
        update(OrganizationMember)
        .where(OrganizationMember.user_id == user_id)
        .values(role="member")
    )
    await db_session.flush()

    search_response = await client.post(
        "/api/v1/search/semantic", headers=headers, json={"query": "anything"}
    )
    assert search_response.status_code == 200

    reindex_response = await client.post("/api/v1/search/reindex", headers=headers)
    assert reindex_response.status_code == 403
