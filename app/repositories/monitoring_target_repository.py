from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.monitoring_target import MonitoringTarget
from app.schemas.monitoring_target import MonitoringTargetCreate, MonitoringTargetUpdate


class MonitoringTargetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, payload: MonitoringTargetCreate) -> MonitoringTarget:
        data = payload.model_dump(mode="json")
        data["url"] = str(payload.url)
        target = MonitoringTarget(**data)
        self.session.add(target)
        await self.session.flush()
        return target

    async def get(self, target_id: UUID) -> MonitoringTarget | None:
        return await self.session.get(MonitoringTarget, target_id)

    async def list_all(self, enabled: bool | None = None) -> list[MonitoringTarget]:
        statement: Select[tuple[MonitoringTarget]] = select(MonitoringTarget).order_by(
            MonitoringTarget.name
        )
        if enabled is not None:
            statement = statement.where(MonitoringTarget.enabled.is_(enabled))
        result = await self.session.scalars(statement)
        return list(result.all())

    async def list_due_ids(self, now: datetime | None = None) -> list[UUID]:
        current_time = now or datetime.now(UTC)
        statement = (
            select(MonitoringTarget.id)
            .where(
                MonitoringTarget.enabled.is_(True),
                MonitoringTarget.next_check_at <= current_time,
            )
            .order_by(MonitoringTarget.next_check_at)
        )
        result = await self.session.scalars(statement)
        return list(result.all())

    async def update(
        self,
        target: MonitoringTarget,
        payload: MonitoringTargetUpdate,
    ) -> MonitoringTarget:
        changes = payload.model_dump(exclude_unset=True, mode="json")
        if payload.url is not None:
            changes["url"] = str(payload.url)
        for field_name, value in changes.items():
            setattr(target, field_name, value)
        await self.session.flush()
        return target

    async def delete(self, target: MonitoringTarget) -> None:
        await self.session.delete(target)
