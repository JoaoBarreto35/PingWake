from typing import Any
from uuid import UUID

import httpx
from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.enums import CheckStatus, Environment, HttpMethod, MonitoringMode, TargetType
from app.db.models.monitoring_target import MonitoringTarget
from app.services.http_checker import HttpChecker
from app.services.request_config_service import RequestConfigService

HEADERS = {"X-PingWake-Key": "test-api-key-with-enough-length"}


async def test_target_secrets_are_encrypted_and_redacted(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    payload = {
        "name": "Supabase database health",
        "url": "https://project.supabase.co/rest/v1/rpc/ping_health",
        "target_type": "database",
        "monitoring_mode": "database_activity",
        "environment": "production",
        "provider": "Supabase",
        "http_method": "POST",
        "expected_status_code": 200,
        "interval_minutes": 720,
        "timeout_seconds": 20,
        "enabled": True,
        "request_headers": {"apikey": "sb_publishable_super-secret-value"},
        "request_body": {},
    }

    response = await client.post("/api/v1/targets", json=payload, headers=HEADERS)

    assert response.status_code == 201
    data = response.json()
    assert data["has_custom_headers"] is True
    assert data["has_request_body"] is True
    assert "request_headers" not in data
    assert "request_body" not in data
    assert "super-secret-value" not in response.text

    target = await session.get(MonitoringTarget, UUID(data["id"]))
    assert target is not None
    assert target.request_headers_encrypted is not None
    assert "super-secret-value" not in target.request_headers_encrypted
    assert target.request_body_encrypted is not None

    request_config = RequestConfigService(get_settings())
    assert request_config.get_headers(target) == {"apikey": "sb_publishable_super-secret-value"}
    assert request_config.get_body(target) == {}


async def test_update_preserves_or_clears_encrypted_configuration(
    client: AsyncClient,
) -> None:
    create_response = await client.post(
        "/api/v1/targets",
        headers=HEADERS,
        json={
            "name": "Supabase target",
            "url": "https://project.supabase.co/rest/v1/rpc/ping_health",
            "http_method": "POST",
            "request_headers": {"apikey": "sb_publishable_value"},
            "request_body": {},
        },
    )
    target_id = create_response.json()["id"]

    preserve_response = await client.patch(
        f"/api/v1/targets/{target_id}",
        headers=HEADERS,
        json={"name": "Renamed Supabase target"},
    )
    assert preserve_response.status_code == 200
    assert preserve_response.json()["has_custom_headers"] is True
    assert preserve_response.json()["has_request_body"] is True

    clear_response = await client.patch(
        f"/api/v1/targets/{target_id}",
        headers=HEADERS,
        json={"request_headers": None, "request_body": None},
    )
    assert clear_response.status_code == 200
    assert clear_response.json()["has_custom_headers"] is False
    assert clear_response.json()["has_request_body"] is False


async def test_invalid_header_is_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/targets",
        headers=HEADERS,
        json={
            "name": "Unsafe header target",
            "url": "https://example.com/health",
            "request_headers": {"apikey": "valid\r\nX-Injected: yes"},
        },
    )
    assert response.status_code == 422


async def test_http_checker_sends_decrypted_headers_and_json_body(
    monkeypatch: Any,
) -> None:
    captured: dict[str, Any] = {}

    class FakeAsyncClient:
        def __init__(self, **_: Any) -> None:
            pass

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *_: Any) -> None:
            return None

        async def request(
            self,
            method: str,
            url: str,
            *,
            headers: dict[str, str],
            json: Any = None,
        ) -> Response:
            captured.update(
                {
                    "method": method,
                    "url": url,
                    "headers": headers,
                    "json": json,
                }
            )
            return Response(200, request=httpx.Request(method, url))

    async def skip_runtime_validation(_: str, __: Any) -> None:
        return None

    monkeypatch.setattr("app.services.http_checker.httpx.AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(
        "app.services.http_checker.validate_target_url_runtime",
        skip_runtime_validation,
    )

    target = MonitoringTarget(
        name="Supabase RPC",
        target_type=TargetType.DATABASE,
        monitoring_mode=MonitoringMode.DATABASE_ACTIVITY,
        environment=Environment.PRODUCTION,
        url="https://project.supabase.co/rest/v1/rpc/ping_health",
        http_method=HttpMethod.POST,
        expected_status_code=200,
        interval_minutes=720,
        timeout_seconds=20,
        enabled=True,
    )
    request_config = RequestConfigService(get_settings())
    request_config.set_headers(target, {"apikey": "sb_publishable_value"})
    request_config.set_body(target, {})

    result = await HttpChecker(get_settings()).check(target)

    assert result.status is CheckStatus.HEALTHY
    assert captured["method"] == "POST"
    assert captured["headers"]["apikey"] == "sb_publishable_value"
    assert captured["json"] == {}
