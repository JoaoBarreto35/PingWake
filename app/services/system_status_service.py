from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.enums import NotificationStatus
from app.db.models.notification_event import NotificationEvent
from app.repositories.scheduler_run_repository import SchedulerRunRepository
from app.schemas.system import ReliabilitySummaryResponse, SchedulerStatusResponse


class SystemStatusService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def build(self, session: AsyncSession) -> ReliabilitySummaryResponse:
        latest = await SchedulerRunRepository(session).latest()
        stale_after_seconds = max(
            60,
            round(
                self.settings.cron_expected_interval_minutes
                * 60
                * self.settings.cron_stale_after_multiplier
            ),
        )
        now = datetime.now(UTC)
        seconds_since_last_run: int | None = None
        scheduler_status = "never"
        if latest is not None:
            started_at = latest.started_at
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=UTC)
            seconds_since_last_run = max(0, int((now - started_at).total_seconds()))
            scheduler_status = (
                "stale" if seconds_since_last_run > stale_after_seconds else "healthy"
            )

        pending_statement = select(func.count(NotificationEvent.id)).where(
            NotificationEvent.status.in_([NotificationStatus.PENDING, NotificationStatus.RETRYING])
        )
        pending_retries = int(await session.scalar(pending_statement) or 0)

        scheduler = SchedulerStatusResponse(
            status=scheduler_status,
            expected_interval_minutes=self.settings.cron_expected_interval_minutes,
            stale_after_seconds=stale_after_seconds,
            last_run_id=latest.id if latest else None,
            last_run_status=latest.status if latest else None,
            last_run_started_at=latest.started_at if latest else None,
            last_run_finished_at=latest.finished_at if latest else None,
            seconds_since_last_run=seconds_since_last_run,
            selected_targets=latest.selected_targets if latest else 0,
            completed_targets=latest.completed_targets if latest else 0,
            retried_notifications=latest.retried_notifications if latest else 0,
            pending_notification_retries=pending_retries,
        )
        return ReliabilitySummaryResponse(
            service=self.settings.app_name,
            version=self.settings.app_version,
            scheduler=scheduler,
            check_retention_days=self.settings.check_retention_days,
            notification_retention_days=self.settings.notification_retention_days,
        )
