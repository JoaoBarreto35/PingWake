from httpx import AsyncClient

HEADERS = {"X-PingWake-Key": "test-api-key-with-enough-length"}


async def test_create_and_list_target(client: AsyncClient) -> None:
    payload = {
        "name": "Example API",
        "url": "https://example.com/health",
        "target_type": "api",
        "monitoring_mode": "monitor",
        "environment": "production",
        "http_method": "GET",
        "expected_status_code": 200,
        "interval_minutes": 30,
        "timeout_seconds": 10,
        "enabled": True,
    }

    create_response = await client.post("/api/v1/targets", json=payload, headers=HEADERS)
    assert create_response.status_code == 201
    assert create_response.json()["name"] == "Example API"

    list_response = await client.get("/api/v1/targets", headers=HEADERS)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


async def test_targets_require_api_key(client: AsyncClient) -> None:
    response = await client.get("/api/v1/targets")
    assert response.status_code == 401


async def test_private_target_is_rejected(client: AsyncClient) -> None:
    payload = {
        "name": "Forbidden local API",
        "url": "http://127.0.0.1:8000/health",
    }
    response = await client.post("/api/v1/targets", json=payload, headers=HEADERS)
    assert response.status_code == 422
