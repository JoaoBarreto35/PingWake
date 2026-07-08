from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.check_run import CheckRun


class CheckRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, check_run: CheckRun) -> CheckRun:
        self.session.add(check_run)
        await self.session.flush()
        return check_run

    async def get(self, check_run_id: UUID) -> CheckRun | None:
        return await self.session.get(CheckRun, check_run_id)

    async def delete_older_than(self, cutoff: datetime) -> int:
        ids_result = await self.session.scalars(
            select(CheckRun.id).where(CheckRun.started_at < cutoff)
        )
        ids = list(ids_result.all())
        if ids:
            await self.session.execute(delete(CheckRun).where(CheckRun.id.in_(ids)))
        return len(ids)

    async def list_by_target(self, target_id: UUID, limit: int = 50) -> list[CheckRun]:
        statement = (
            select(CheckRun)
            .where(CheckRun.target_id == target_id)
            .order_by(CheckRun.started_at.desc())
            .limit(limit)
        )
        result = await self.session.scalars(statement)
        return list(result.all())
