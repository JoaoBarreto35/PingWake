from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.enums import CheckStatus
from app.db.models.check_run import CheckRun
from app.db.models.monitoring_target import MonitoringTarget
from app.repositories.incident_repository import IncidentRepository
from app.services.incident_service import IncidentService


async def test_incident_opens_after_three_failures(session: AsyncSession) -> None:
    target = MonitoringTarget(name="API", url="https://example.com/health")
    session.add(target)
    await session.flush()

    service = IncidentService(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            failures_to_open_incident=3,
            successes_to_resolve_incident=2,
        )
    )

    for attempt in range(3):
        now = datetime.now(UTC)
        run = CheckRun(
            target_id=target.id,
            status=CheckStatus.UNHEALTHY,
            started_at=now,
            finished_at=now,
            attempt_number=attempt + 1,
            trigger_source="test",
        )
        session.add(run)
        await session.flush()
        await service.apply_check_result(session, target, run)

    repository = IncidentRepository(session)
    incident = await repository.get_open_by_target(target.id)

    assert incident is not None
    assert incident.consecutive_failures == 3


async def test_incident_resolves_after_two_successes(session: AsyncSession) -> None:
    target = MonitoringTarget(name="API", url="https://example.com/health")
    session.add(target)
    await session.flush()

    service = IncidentService(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            failures_to_open_incident=1,
            successes_to_resolve_incident=2,
        )
    )

    now = datetime.now(UTC)
    failed_run = CheckRun(
        target_id=target.id,
        status=CheckStatus.UNHEALTHY,
        started_at=now,
        finished_at=now,
        attempt_number=1,
        trigger_source="test",
    )
    session.add(failed_run)
    await session.flush()
    opened_transition = await service.apply_check_result(session, target, failed_run)
    assert opened_transition is not None

    for attempt in range(2):
        healthy_run = CheckRun(
            target_id=target.id,
            status=CheckStatus.HEALTHY,
            http_status_code=200,
            started_at=now,
            finished_at=now,
            attempt_number=attempt + 2,
            trigger_source="test",
        )
        session.add(healthy_run)
        await session.flush()
        resolved_transition = await service.apply_check_result(session, target, healthy_run)

    assert resolved_transition is not None
    assert resolved_transition.event_type.value == "incident_resolved"
    assert resolved_transition.incident.status.value == "resolved"
    assert resolved_transition.incident.resolved_at is not None
