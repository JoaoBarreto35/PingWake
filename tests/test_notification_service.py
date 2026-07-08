from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.enums import (
    CheckStatus,
    IncidentStatus,
    NotificationEventType,
    NotificationStatus,
)
from app.db.models.check_run import CheckRun
from app.db.models.incident import Incident
from app.db.models.monitoring_target import MonitoringTarget
from app.db.models.notification_event import NotificationEvent
from app.services.incident_service import IncidentTransition
from app.services.notification_service import NotificationService


async def create_incident_context(
    session: AsyncSession,
) -> tuple[MonitoringTarget, CheckRun, Incident]:
    now = datetime.now(UTC)
    target = MonitoringTarget(
        name="Prumo Backend",
        project_name="Prumo",
        provider="Render",
        url="https://example.com/health",
    )
    session.add(target)
    await session.flush()

    check_run = CheckRun(
        target_id=target.id,
        status=CheckStatus.UNHEALTHY,
        http_status_code=503,
        latency_ms=900,
        started_at=now,
        finished_at=now,
        attempt_number=1,
        trigger_source="test",
        error_type="UnexpectedStatusCode",
        error_message="Expected 200, received 503.",
    )
    session.add(check_run)
    await session.flush()

    incident = Incident(
        target_id=target.id,
        status=IncidentStatus.OPEN,
        started_at=now,
        first_failure_run_id=check_run.id,
        last_failure_run_id=check_run.id,
        consecutive_failures=3,
        consecutive_successes=0,
        summary="Prumo Backend failed 3 consecutive checks.",
    )
    session.add(incident)
    await session.commit()
    return target, check_run, incident


async def test_discord_notification_is_sent_and_logged(session: AsyncSession) -> None:
    target, check_run, incident = await create_incident_context(session)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "discord.com"
        return httpx.Response(status_code=204, request=request)

    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        notifications_enabled=True,
        discord_webhook_url="https://discord.com/api/webhooks/123/test-token",
    )
    service = NotificationService(settings, transport=httpx.MockTransport(handler))
    transition = IncidentTransition(
        incident=incident,
        event_type=NotificationEventType.INCIDENT_OPENED,
    )

    event = await service.notify_incident_transition(session, target, check_run, transition)

    assert event is not None
    assert event.status is NotificationStatus.SENT
    assert event.sent_at is not None
    assert event.error_message is None

    stored_event = await session.scalar(select(NotificationEvent))
    assert stored_event is not None
    assert stored_event.event_type is NotificationEventType.INCIDENT_OPENED


async def test_discord_failure_is_logged_without_raising(session: AsyncSession) -> None:
    target, check_run, incident = await create_incident_context(session)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=500, request=request)

    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        notifications_enabled=True,
        discord_webhook_url="https://discord.com/api/webhooks/123/test-token",
    )
    service = NotificationService(settings, transport=httpx.MockTransport(handler))
    transition = IncidentTransition(
        incident=incident,
        event_type=NotificationEventType.INCIDENT_OPENED,
    )

    event = await service.notify_incident_transition(session, target, check_run, transition)

    assert event is not None
    assert event.status is NotificationStatus.RETRYING
    assert event.sent_at is None
    assert event.error_message == "Discord returned HTTP 500."
    assert event.attempt_count == 1
    assert event.next_retry_at is not None
