import asyncio
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.enums import CheckStatus
from app.db.models.check_run import CheckRun
from app.db.models.monitoring_target import MonitoringTarget
from app.db.session import async_session_factory
from app.repositories.check_run_repository import CheckRunRepository
from app.repositories.monitoring_target_repository import MonitoringTargetRepository
from app.services.http_checker import HttpChecker
from app.services.incident_service import IncidentService

logger = logging.getLogger(__name__)


class CheckRunner:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.http_checker = HttpChecker(self.settings)
        self.incident_service = IncidentService(self.settings)

    async def run_target(
        self,
        session: AsyncSession,
        target: MonitoringTarget,
        trigger_source: str,
    ) -> CheckRun:
        result = await self.http_checker.check(target)
        check_run = CheckRun(
            target_id=target.id,
            status=result.status,
            http_status_code=result.http_status_code,
            latency_ms=result.latency_ms,
            started_at=result.started_at,
            finished_at=result.finished_at,
            attempt_number=1,
            trigger_source=trigger_source,
            error_type=result.error_type,
            error_message=result.error_message,
        )

        repository = CheckRunRepository(session)
        await repository.create(check_run)

        target.last_status = result.status
        target.last_checked_at = result.finished_at
        target.next_check_at = result.finished_at + timedelta(minutes=target.interval_minutes)

        await self.incident_service.apply_check_result(session, target, check_run)
        await session.commit()
        await session.refresh(check_run)
        return check_run

    async def run_due_targets(self) -> dict[str, int]:
        async with async_session_factory() as session:
            repository = MonitoringTargetRepository(session)
            target_ids = await repository.list_due_ids(datetime.now(UTC))

        semaphore = asyncio.Semaphore(self.settings.max_concurrency)

        async def execute(target_id: UUID) -> CheckStatus | None:
            async with semaphore:
                try:
                    async with async_session_factory() as session:
                        repository = MonitoringTargetRepository(session)
                        target = await repository.get(target_id)
                        if target is None or not target.enabled:
                            return None
                        check_run = await self.run_target(session, target, trigger_source="cron")
                        return check_run.status
                except Exception:
                    logger.exception(
                        "Scheduled check failed before completion",
                        extra={"target_id": str(target_id)},
                    )
                    return None

        statuses = await asyncio.gather(*(execute(target_id) for target_id in target_ids))
        completed_statuses = [item for item in statuses if item is not None]
        healthy = sum(item is CheckStatus.HEALTHY for item in completed_statuses)
        return {
            "selected": len(target_ids),
            "completed": len(completed_statuses),
            "healthy": healthy,
            "failed": len(completed_statuses) - healthy,
        }
