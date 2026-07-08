import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.enums import (
    NotificationChannel,
    NotificationEventType,
    NotificationStatus,
)
from app.db.models.check_run import CheckRun
from app.db.models.incident import Incident
from app.db.models.monitoring_target import MonitoringTarget
from app.db.models.notification_event import NotificationEvent
from app.repositories.check_run_repository import CheckRunRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.monitoring_target_repository import MonitoringTargetRepository
from app.repositories.notification_event_repository import NotificationEventRepository
from app.services.incident_service import IncidentTransition

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(
        self,
        settings: Settings | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.transport = transport

    async def notify_incident_transition(
        self,
        session: AsyncSession,
        target: MonitoringTarget,
        check_run: CheckRun,
        transition: IncidentTransition,
    ) -> NotificationEvent | None:
        if not self.settings.notifications_enabled:
            return None

        repository = NotificationEventRepository(session)
        existing = await repository.get_for_transition(
            transition.incident.id,
            transition.event_type,
        )
        if existing is not None:
            return existing

        now = datetime.now(UTC)
        notification_event = NotificationEvent(
            incident_id=transition.incident.id,
            target_id=target.id,
            event_type=transition.event_type,
            channel=NotificationChannel.DISCORD,
            status=NotificationStatus.PENDING,
            attempt_count=0,
            max_attempts=self.settings.notification_max_attempts,
            next_retry_at=now,
        )
        await repository.create(notification_event)
        await session.commit()
        await session.refresh(notification_event)
        return await self._attempt_event(
            session,
            notification_event,
            target,
            check_run,
            transition.incident,
        )

    async def retry_due_notifications(self, session: AsyncSession, limit: int = 100) -> int:
        repository = NotificationEventRepository(session)
        events = await repository.list_due_retries(datetime.now(UTC), limit=limit)
        attempted = 0
        for event in events:
            if await self.retry_event(session, event.id) is not None:
                attempted += 1
        return attempted

    async def retry_event(
        self,
        session: AsyncSession,
        notification_id: UUID,
        *,
        force: bool = False,
    ) -> NotificationEvent | None:
        repository = NotificationEventRepository(session)
        event = await repository.get(notification_id)
        if event is None:
            return None
        if event.status is NotificationStatus.SENT:
            return event
        if event.attempt_count >= event.max_attempts and not force:
            return event

        incident = await IncidentRepository(session).get(event.incident_id)
        target = await MonitoringTargetRepository(session).get(event.target_id)
        if incident is None or target is None:
            event.status = NotificationStatus.FAILED
            event.next_retry_at = None
            event.error_message = "Incident or target no longer exists."
            await session.commit()
            return event

        check_run = await self._resolve_check_run(session, event, incident)
        if check_run is None:
            event.status = NotificationStatus.FAILED
            event.next_retry_at = None
            event.error_message = "No check run is available to rebuild the notification."
            await session.commit()
            return event

        if force and event.attempt_count >= event.max_attempts:
            event.max_attempts = event.attempt_count + 1

        return await self._attempt_event(session, event, target, check_run, incident)

    async def _resolve_check_run(
        self,
        session: AsyncSession,
        event: NotificationEvent,
        incident: Incident,
    ) -> CheckRun | None:
        check_repository = CheckRunRepository(session)
        if event.event_type is NotificationEventType.INCIDENT_OPENED:
            return await check_repository.get(incident.last_failure_run_id)
        checks = await check_repository.list_by_target(event.target_id, limit=1)
        return checks[0] if checks else None

    async def _attempt_event(
        self,
        session: AsyncSession,
        event: NotificationEvent,
        target: MonitoringTarget,
        check_run: CheckRun,
        incident: Incident,
    ) -> NotificationEvent:
        now = datetime.now(UTC)
        event.attempt_count += 1
        event.last_attempt_at = now
        event.status = NotificationStatus.RETRYING
        event.next_retry_at = None

        try:
            webhook_url = self._get_webhook_url()
            payload = self._build_discord_payload(target, check_run, incident, event.event_type)
            timeout = httpx.Timeout(float(self.settings.notification_timeout_seconds))
            async with httpx.AsyncClient(
                timeout=timeout,
                transport=self.transport,
                headers={"User-Agent": f"PingWake/{self.settings.app_version}"},
            ) as client:
                response = await client.post(webhook_url, json=payload)
                response.raise_for_status()

            event.status = NotificationStatus.SENT
            event.sent_at = datetime.now(UTC)
            event.error_message = None
        except Exception as exc:
            event.error_message = self._safe_error_message(exc)
            if event.attempt_count >= event.max_attempts:
                event.status = NotificationStatus.FAILED
                event.next_retry_at = None
            else:
                event.status = NotificationStatus.RETRYING
                event.next_retry_at = now + timedelta(
                    seconds=self._retry_delay(event.attempt_count)
                )
            logger.warning(
                "Discord incident notification failed",
                extra={
                    "notification_id": str(event.id),
                    "incident_id": str(incident.id),
                    "target_id": str(target.id),
                    "event_type": event.event_type.value,
                    "attempt_count": event.attempt_count,
                },
            )

        await session.commit()
        await session.refresh(event)
        return event

    def _retry_delay(self, attempt_count: int) -> int:
        delays = self.settings.notification_retry_delays
        index = min(max(0, attempt_count - 1), len(delays) - 1)
        return delays[index]

    def _get_webhook_url(self) -> str:
        if self.settings.discord_webhook_url is None:
            raise RuntimeError("Discord webhook is not configured.")
        return self.settings.discord_webhook_url.get_secret_value()

    def _build_discord_payload(
        self,
        target: MonitoringTarget,
        check_run: CheckRun,
        incident: Incident,
        event_type: NotificationEventType,
    ) -> dict[str, Any]:
        project_name = target.project_name or "Sem projeto informado"
        provider = target.provider or "Não informado"

        if event_type is NotificationEventType.INCIDENT_OPENED:
            title = "🔴 Serviço indisponível"
            description = (
                f"O PingWake confirmou **{incident.consecutive_failures} falhas consecutivas** "
                "e abriu um incidente."
            )
            color = 15_158_332
            fields = [
                {"name": "Projeto", "value": project_name, "inline": True},
                {"name": "Serviço", "value": target.name, "inline": True},
                {"name": "Ambiente", "value": target.environment.value, "inline": True},
                {"name": "Provedor", "value": provider, "inline": True},
                {
                    "name": "HTTP",
                    "value": str(check_run.http_status_code or "Sem resposta"),
                    "inline": True,
                },
                {
                    "name": "Latência",
                    "value": self._format_latency(check_run.latency_ms),
                    "inline": True,
                },
                {
                    "name": "Erro",
                    "value": self._truncate(
                        check_run.error_message or check_run.error_type or "Resposta inesperada",
                        900,
                    ),
                    "inline": False,
                },
            ]
        else:
            title = "🟢 Serviço recuperado"
            duration = self._format_duration(incident.started_at, incident.resolved_at)
            description = (
                "O serviço voltou a responder corretamente e o incidente foi resolvido "
                f"após **{duration}**."
            )
            color = 3_066_993
            fields = [
                {"name": "Projeto", "value": project_name, "inline": True},
                {"name": "Serviço", "value": target.name, "inline": True},
                {"name": "Ambiente", "value": target.environment.value, "inline": True},
                {"name": "Duração", "value": duration, "inline": True},
                {
                    "name": "HTTP",
                    "value": str(check_run.http_status_code or "Sem resposta"),
                    "inline": True,
                },
                {
                    "name": "Latência",
                    "value": self._format_latency(check_run.latency_ms),
                    "inline": True,
                },
            ]

        return {
            "username": "PingWake",
            "allowed_mentions": {"parse": []},
            "embeds": [
                {
                    "title": title,
                    "description": description,
                    "color": color,
                    "fields": fields,
                    "footer": {"text": f"PingWake • Incidente {incident.id}"},
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            ],
        }

    @staticmethod
    def _format_latency(latency_ms: int | None) -> str:
        return f"{latency_ms} ms" if latency_ms is not None else "Não medida"

    @staticmethod
    def _format_duration(started_at: datetime, resolved_at: datetime | None) -> str:
        end = resolved_at or datetime.now(UTC)
        start = started_at if started_at.tzinfo is not None else started_at.replace(tzinfo=UTC)
        if end.tzinfo is None:
            end = end.replace(tzinfo=UTC)
        total_seconds = max(0, int((end - start).total_seconds()))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}h {minutes}min"
        if minutes:
            return f"{minutes}min {seconds}s"
        return f"{seconds}s"

    @staticmethod
    def _truncate(value: str, limit: int) -> str:
        return value if len(value) <= limit else f"{value[: limit - 1]}…"

    @staticmethod
    def _safe_error_message(exc: Exception) -> str:
        if isinstance(exc, httpx.HTTPStatusError):
            return f"Discord returned HTTP {exc.response.status_code}."
        if isinstance(exc, httpx.TimeoutException):
            return "Discord webhook request timed out."
        if isinstance(exc, httpx.HTTPError):
            return f"Discord webhook request failed: {type(exc).__name__}."
        return f"Notification failed: {type(exc).__name__}."
