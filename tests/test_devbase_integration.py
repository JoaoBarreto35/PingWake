from httpx import AsyncClient

HEADERS = {"X-PingWake-Key": "test-api-key-with-enough-length"}


async def test_devbase_summary_returns_target_state(client: AsyncClient) -> None:
    payload = {
        "name": "Prumo Backend",
        "project_name": "Prumo",
        "url": "https://example.com/health",
        "target_type": "api",
        "monitoring_mode": "keep_awake",
        "environment": "production",
        "expected_status_code": 200,
        "interval_minutes": 5,
        "timeout_seconds": 70,
        "enabled": True,
    }
    created = await client.post("/api/v1/targets", json=payload, headers=HEADERS)
    assert created.status_code == 201
    target_id = created.json()["id"]

    response = await client.get(
        f"/api/v1/integrations/devbase/targets/{target_id}",
        headers=HEADERS,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Prumo Backend"
    assert body["project_name"] == "Prumo"
    assert body["status"] == "pending"
    assert body["open_incident"] is False
    assert body["latency_ms"] is None


async def test_devbase_summary_requires_api_key(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/integrations/devbase/targets/e93bc86e-c548-4aa4-ada0-3e555caf2e65"
    )
    assert response.status_code == 401
