from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.repositories.check_run_repository import CheckRunRepository
from app.repositories.notification_event_repository import NotificationEventRepository
from app.repositories.scheduler_run_repository import SchedulerRunRepository


@dataclass(frozen=True, slots=True)
class RetentionResult:
    check_runs: int = 0
    notifications: int = 0
    scheduler_runs: int = 0


class RetentionService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def prune(self, session: AsyncSession) -> RetentionResult:
        now = datetime.now(UTC)
        check_runs = await CheckRunRepository(session).delete_older_than(
            now - timedelta(days=self.settings.check_retention_days)
        )
        notifications = await NotificationEventRepository(session).delete_older_than(
            now - timedelta(days=self.settings.notification_retention_days)
        )
        scheduler_runs = await SchedulerRunRepository(session).delete_older_than(
            now - timedelta(days=self.settings.scheduler_run_retention_days)
        )
        await session.commit()
        return RetentionResult(
            check_runs=check_runs,
            notifications=notifications,
            scheduler_runs=scheduler_runs,
        )
