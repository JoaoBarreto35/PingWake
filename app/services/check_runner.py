import asyncio
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.enums import CheckStatus, SchedulerRunStatus
from app.db.models.check_run import CheckRun
from app.db.models.monitoring_target import MonitoringTarget
from app.db.models.scheduler_run import SchedulerRun
from app.db.session import async_session_factory
from app.repositories.check_run_repository import CheckRunRepository
from app.repositories.monitoring_target_repository import MonitoringTargetRepository
from app.repositories.scheduler_run_repository import SchedulerRunRepository
from app.services.http_checker import HttpChecker
from app.services.incident_service import IncidentService
from app.services.notification_service import NotificationService
from app.services.retention_service import RetentionService

logger = logging.getLogger(__name__)


class CheckRunner:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.http_checker = HttpChecker(self.settings)
        self.incident_service = IncidentService(self.settings)
        self.notification_service = NotificationService(self.settings)
        self.retention_service = RetentionService(self.settings)

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

        transition = await self.incident_service.apply_check_result(session, target, check_run)

        # Monitoring data is committed before external notifications. Discord must never
        # be able to roll back a check or incident transition.
        await session.commit()
        await session.refresh(check_run)

        if transition is not None:
            await self.notification_service.notify_incident_transition(
                session,
                target,
                check_run,
                transition,
            )

        return check_run

    async def run_due_targets(self) -> dict[str, int | str]:
        scheduler_run = await self._start_scheduler_run()
        try:
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
                            check_run = await self.run_target(
                                session, target, trigger_source="cron"
                            )
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
            degraded = sum(item is CheckStatus.DEGRADED for item in completed_statuses)
            target_failures = len(completed_statuses) - healthy - degraded

            async with async_session_factory() as session:
                retried = await self.notification_service.retry_due_notifications(session)
                retention = await self.retention_service.prune(session)

            result: dict[str, int | str] = {
                "scheduler_run_id": str(scheduler_run.id),
                "selected": len(target_ids),
                "completed": len(completed_statuses),
                "healthy": healthy,
                "degraded": degraded,
                "failed": target_failures,
                "retried_notifications": retried,
                "pruned_check_runs": retention.check_runs,
                "pruned_notifications": retention.notifications,
            }
            await self._finish_scheduler_run(
                scheduler_run.id,
                result,
                partial=len(completed_statuses) < len(target_ids),
            )
            return result
        except Exception as exc:
            await self._fail_scheduler_run(scheduler_run.id, exc)
            raise

    async def _start_scheduler_run(self) -> SchedulerRun:
        async with async_session_factory() as session:
            run = SchedulerRun(status=SchedulerRunStatus.RUNNING)
            await SchedulerRunRepository(session).create(run)
            await session.commit()
            await session.refresh(run)
            return run

    async def _finish_scheduler_run(
        self,
        run_id: UUID,
        result: dict[str, int | str],
        *,
        partial: bool,
    ) -> None:
        async with async_session_factory() as session:
            run = await session.get(SchedulerRun, run_id)
            if run is None:
                return
            run.status = SchedulerRunStatus.PARTIAL if partial else SchedulerRunStatus.COMPLETED
            run.finished_at = datetime.now(UTC)
            run.selected_targets = int(result["selected"])
            run.completed_targets = int(result["completed"])
            run.healthy_targets = int(result["healthy"])
            run.failed_targets = int(result["failed"])
            run.retried_notifications = int(result["retried_notifications"])
            run.pruned_check_runs = int(result["pruned_check_runs"])
            run.pruned_notifications = int(result["pruned_notifications"])
            await session.commit()

    async def _fail_scheduler_run(self, run_id: UUID, exc: Exception) -> None:
        async with async_session_factory() as session:
            run = await session.get(SchedulerRun, run_id)
            if run is None:
                return
            run.status = SchedulerRunStatus.FAILED
            run.finished_at = datetime.now(UTC)
            run.error_message = f"{type(exc).__name__}: {str(exc)[:500]}"
            await session.commit()
