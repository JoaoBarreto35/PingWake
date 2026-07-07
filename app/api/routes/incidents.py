from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_api_key
from app.core.enums import IncidentStatus
from app.repositories.incident_repository import IncidentRepository
from app.schemas.incident import IncidentResponse

router = APIRouter(
    prefix="/api/v1/incidents",
    tags=["Incidents"],
    dependencies=[Depends(require_api_key)],
)


@router.get("", response_model=list[IncidentResponse])
async def list_incidents(
    incident_status: IncidentStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
) -> list[IncidentResponse]:
    repository = IncidentRepository(session)
    incidents = await repository.list_all(status_filter=incident_status, limit=limit)
    return [IncidentResponse.model_validate(incident) for incident in incidents]


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> IncidentResponse:
    repository = IncidentRepository(session)
    incident = await repository.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")
    return IncidentResponse.model_validate(incident)
