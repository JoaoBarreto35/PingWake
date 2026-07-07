from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.enums import CheckStatus, IncidentStatus, NotificationEventType
from app.db.models.check_run import CheckRun
from app.db.models.incident import Incident
from app.db.models.monitoring_target import MonitoringTarget
from app.repositories.incident_repository import IncidentRepository


@dataclass(slots=True)
class IncidentTransition:
    incident: Incident
    event_type: NotificationEventType


class IncidentService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def apply_check_result(
        self,
        session: AsyncSession,
        target: MonitoringTarget,
        check_run: CheckRun,
    ) -> IncidentTransition | None:
        repository = IncidentRepository(session)
        open_incident = await repository.get_open_by_target(target.id)

        if check_run.status is CheckStatus.HEALTHY:
            target.consecutive_successes += 1
            target.consecutive_failures = 0
            if open_incident is not None:
                open_incident.consecutive_successes = target.consecutive_successes
                if target.consecutive_successes >= self.settings.successes_to_resolve_incident:
                    open_incident.status = IncidentStatus.RESOLVED
                    open_incident.resolved_at = datetime.now(UTC)
                    return IncidentTransition(
                        incident=open_incident,
                        event_type=NotificationEventType.INCIDENT_RESOLVED,
                    )
            return None

        target.consecutive_failures += 1
        target.consecutive_successes = 0

        if open_incident is not None:
            open_incident.last_failure_run_id = check_run.id
            open_incident.consecutive_failures = target.consecutive_failures
            open_incident.consecutive_successes = 0
            return None

        if target.consecutive_failures < self.settings.failures_to_open_incident:
            return None

        recent_failures_statement = (
            select(CheckRun)
            .where(
                CheckRun.target_id == target.id,
                CheckRun.status != CheckStatus.HEALTHY,
            )
            .order_by(CheckRun.started_at.desc())
            .limit(target.consecutive_failures)
        )
        recent_failures_result = await session.scalars(recent_failures_statement)
        recent_failures = list(recent_failures_result.all())
        first_failure = recent_failures[-1] if recent_failures else check_run

        incident = Incident(
            target_id=target.id,
            status=IncidentStatus.OPEN,
            started_at=first_failure.started_at,
            first_failure_run_id=first_failure.id,
            last_failure_run_id=check_run.id,
            consecutive_failures=target.consecutive_failures,
            consecutive_successes=0,
            summary=f"{target.name} failed {target.consecutive_failures} consecutive checks.",
        )
        await repository.create(incident)
        return IncidentTransition(
            incident=incident,
            event_type=NotificationEventType.INCIDENT_OPENED,
        )
