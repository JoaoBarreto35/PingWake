from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.check_run import CheckRun


class CheckRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, check_run: CheckRun) -> CheckRun:
        self.session.add(check_run)
        await self.session.flush()
        return check_run

    async def list_by_target(self, target_id: UUID, limit: int = 50) -> list[CheckRun]:
        statement = (
            select(CheckRun)
            .where(CheckRun.target_id == target_id)
            .order_by(CheckRun.started_at.desc())
            .limit(limit)
        )
        result = await self.session.scalars(statement)
        return list(result.all())
