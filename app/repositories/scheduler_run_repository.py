from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.scheduler_run import SchedulerRun


class SchedulerRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, run: SchedulerRun) -> SchedulerRun:
        self.session.add(run)
        await self.session.flush()
        return run

    async def latest(self) -> SchedulerRun | None:
        statement = select(SchedulerRun).order_by(SchedulerRun.started_at.desc()).limit(1)
        result = await self.session.scalars(statement)
        return result.first()

    async def delete_older_than(self, cutoff: datetime) -> int:
        ids_result = await self.session.scalars(
            select(SchedulerRun.id).where(SchedulerRun.started_at < cutoff)
        )
        ids = list(ids_result.all())
        if ids:
            await self.session.execute(delete(SchedulerRun).where(SchedulerRun.id.in_(ids)))
        return len(ids)
