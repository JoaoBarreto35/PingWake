from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import IncidentStatus
from app.db.models.incident import Incident


class IncidentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, incident: Incident) -> Incident:
        self.session.add(incident)
        await self.session.flush()
        return incident

    async def get(self, incident_id: UUID) -> Incident | None:
        return await self.session.get(Incident, incident_id)

    async def get_open_by_target(self, target_id: UUID) -> Incident | None:
        statement = select(Incident).where(
            Incident.target_id == target_id,
            Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.ACKNOWLEDGED]),
        )
        result = await self.session.scalars(statement)
        return result.first()

    async def list_all(
        self,
        status_filter: IncidentStatus | None = None,
        limit: int = 100,
    ) -> list[Incident]:
        statement = select(Incident).order_by(Incident.started_at.desc()).limit(limit)
        if status_filter is not None:
            statement = statement.where(Incident.status == status_filter)
        result = await self.session.scalars(statement)
        return list(result.all())
