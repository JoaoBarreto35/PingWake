from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.enums import (
    CheckStatus,
    HttpMethod,
    NotificationEventType,
    NotificationStatus,
    OperationalStatus,
)
from app.db.models.check_run import CheckRun
from app.db.models.incident import Incident
from app.db.models.monitoring_target import MonitoringTarget
from app.services.http_checker import HttpChecker
from app.services.incident_service import IncidentTransition
from app.services.notification_service import NotificationService
from app.services.status_service import StatusService


def test_stale_status_overrides_last_healthy_result() -> None:
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        stale_after_multiplier=2.0,
    )
    target = MonitoringTarget(
        name="API",
        url="https://example.com/health",
        interval_minutes=5,
        enabled=True,
        last_status=CheckStatus.HEALTHY,
        last_checked_at=datetime.now(UTC) - timedelta(minutes=11),
    )

    result = StatusService(settings).evaluate(target)

    assert result.status is OperationalStatus.STALE
    assert result.raw_status == "healthy"
    assert result.is_stale is True


async def test_high_latency_is_degraded() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=200, request=request)

    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        default_degraded_latency_ms=100,
    )
    checker = HttpChecker(settings)
    target = MonitoringTarget(
        name="Slow API",
        url="https://example.com/health",
        http_method=HttpMethod.GET,
        expected_status_code=200,
        timeout_seconds=10,
        has_request_body=False,
        has_custom_headers=False,
        degraded_latency_ms=100,
    )

    original_client = httpx.AsyncClient

    class MockClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            super().__init__(*args, **kwargs)

    httpx.AsyncClient = MockClient
    try:
        with (
            patch("app.services.http_checker.validate_target_url_runtime", new=AsyncMock()),
            patch("app.services.http_checker.perf_counter", side_effect=[0.0, 0.2]),
        ):
            result = await checker.check(target)
    finally:
        httpx.AsyncClient = original_client

    assert result.status is CheckStatus.DEGRADED
    assert result.error_type == "HighLatency"


async def test_failed_notification_can_be_retried(session: AsyncSession) -> None:
    now = datetime.now(UTC)
    target = MonitoringTarget(name="API", url="https://example.com/health")
    session.add(target)
    await session.flush()
    check_run = CheckRun(
        target_id=target.id,
        status=CheckStatus.UNHEALTHY,
        http_status_code=503,
        latency_ms=10,
        started_at=now,
        finished_at=now,
        attempt_number=1,
        trigger_source="test",
    )
    session.add(check_run)
    await session.flush()
    incident = Incident(
        target_id=target.id,
        started_at=now,
        first_failure_run_id=check_run.id,
        last_failure_run_id=check_run.id,
        consecutive_failures=3,
        summary="failed",
    )
    session.add(incident)
    await session.commit()

    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(status_code=500 if calls == 1 else 204, request=request)

    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        notifications_enabled=True,
        discord_webhook_url="https://discord.com/api/webhooks/123/token",
        notification_retry_delays_seconds="1",
    )
    service = NotificationService(settings, transport=httpx.MockTransport(handler))
    event = await service.notify_incident_transition(
        session,
        target,
        check_run,
        IncidentTransition(incident, NotificationEventType.INCIDENT_OPENED),
    )
    assert event is not None
    assert event.status is NotificationStatus.RETRYING

    retried = await service.retry_event(session, event.id, force=True)
    assert retried is not None
    assert retried.status is NotificationStatus.SENT
    assert retried.attempt_count == 2
