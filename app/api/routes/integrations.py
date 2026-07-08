from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_api_key
from app.repositories.check_run_repository import CheckRunRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.monitoring_target_repository import MonitoringTargetRepository
from app.schemas.integration import DevBaseTargetSummary

router = APIRouter(
    prefix="/api/v1/integrations/devbase",
    tags=["Integrations"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/targets/{target_id}", response_model=DevBaseTargetSummary)
async def get_devbase_target_summary(
    target_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> DevBaseTargetSummary:
    target_repository = MonitoringTargetRepository(session)
    target = await target_repository.get(target_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found.")

    checks = await CheckRunRepository(session).list_by_target(target_id, limit=1)
    latest = checks[0] if checks else None
    incident = await IncidentRepository(session).get_open_by_target(target_id)

    return DevBaseTargetSummary(
        id=target.id,
        name=target.name,
        project_name=target.project_name,
        status=target.last_status,
        enabled=target.enabled,
        monitoring_mode=target.monitoring_mode,
        environment=target.environment,
        last_checked_at=target.last_checked_at,
        next_check_at=target.next_check_at,
        latency_ms=latest.latency_ms if latest else None,
        http_status_code=latest.http_status_code if latest else None,
        consecutive_failures=target.consecutive_failures,
        consecutive_successes=target.consecutive_successes,
        open_incident=incident is not None,
        incident_started_at=incident.started_at if incident else None,
        incident_summary=incident.summary if incident else None,
    )
