from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.core.config import Settings, get_settings
from app.core.enums import OperationalStatus
from app.db.models.monitoring_target import MonitoringTarget


@dataclass(frozen=True, slots=True)
class EffectiveTargetStatus:
    status: OperationalStatus
    raw_status: str
    is_stale: bool
    stale_after_seconds: int
    seconds_since_last_check: int | None


class StatusService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def evaluate(
        self,
        target: MonitoringTarget,
        now: datetime | None = None,
    ) -> EffectiveTargetStatus:
        current = now or datetime.now(UTC)
        stale_after_seconds = max(
            60,
            round(target.interval_minutes * 60 * self.settings.stale_after_multiplier),
        )

        if not target.enabled:
            return EffectiveTargetStatus(
                status=OperationalStatus.DISABLED,
                raw_status=target.last_status.value,
                is_stale=False,
                stale_after_seconds=stale_after_seconds,
                seconds_since_last_check=None,
            )

        if target.last_checked_at is None:
            return EffectiveTargetStatus(
                status=OperationalStatus.PENDING,
                raw_status=target.last_status.value,
                is_stale=False,
                stale_after_seconds=stale_after_seconds,
                seconds_since_last_check=None,
            )

        last_checked_at = target.last_checked_at
        if last_checked_at.tzinfo is None:
            last_checked_at = last_checked_at.replace(tzinfo=UTC)
        age_seconds = max(0, int((current - last_checked_at).total_seconds()))
        is_stale = current > last_checked_at + timedelta(seconds=stale_after_seconds)
        if is_stale:
            return EffectiveTargetStatus(
                status=OperationalStatus.STALE,
                raw_status=target.last_status.value,
                is_stale=True,
                stale_after_seconds=stale_after_seconds,
                seconds_since_last_check=age_seconds,
            )

        return EffectiveTargetStatus(
            status=OperationalStatus(target.last_status.value),
            raw_status=target.last_status.value,
            is_stale=False,
            stale_after_seconds=stale_after_seconds,
            seconds_since_last_check=age_seconds,
        )
