from datetime import datetime, timedelta, timezone

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


async def test_priority_queue_scores_and_orders_work_items(client: AsyncClient):
    headers = await _auth_headers(client, "priority-queue@example.com")
    soon = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    later = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()

    urgent_response = await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Acil proposal follow up", "priority": "high", "due_at": soon},
    )
    assert urgent_response.status_code == 201

    low_response = await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Later admin task", "priority": "low", "due_at": later},
    )
    assert low_response.status_code == 201

    response = await client.get("/api/v1/priority/queue", headers=headers)
    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["title"] == "Acil proposal follow up"
    assert items[0]["score"] > items[1]["score"]
    assert {factor["key"] for factor in items[0]["factors"]} >= {
        "explicit_priority",
        "due_soon",
        "urgent_language",
    }
