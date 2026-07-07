import logging
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.enums import (
    NotificationChannel,
    NotificationEventType,
    NotificationStatus,
)
from app.db.models.check_run import CheckRun
from app.db.models.monitoring_target import MonitoringTarget
from app.db.models.notification_event import NotificationEvent
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

        notification_event = NotificationEvent(
            incident_id=transition.incident.id,
            target_id=target.id,
            event_type=transition.event_type,
            channel=NotificationChannel.DISCORD,
            status=NotificationStatus.FAILED,
        )

        try:
            webhook_url = self._get_webhook_url()
            payload = self._build_discord_payload(target, check_run, transition)
            timeout = httpx.Timeout(float(self.settings.notification_timeout_seconds))
            async with httpx.AsyncClient(
                timeout=timeout,
                transport=self.transport,
                headers={"User-Agent": f"PingWake/{self.settings.app_version}"},
            ) as client:
                response = await client.post(webhook_url, json=payload)
                response.raise_for_status()

            notification_event.status = NotificationStatus.SENT
            notification_event.sent_at = datetime.now(UTC)
        except Exception as exc:
            notification_event.error_message = self._safe_error_message(exc)
            logger.warning(
                "Discord incident notification failed",
                extra={
                    "incident_id": str(transition.incident.id),
                    "target_id": str(target.id),
                    "event_type": transition.event_type.value,
                },
            )

        try:
            repository = NotificationEventRepository(session)
            await repository.create(notification_event)
            await session.commit()
            await session.refresh(notification_event)
        except Exception:
            await session.rollback()
            logger.exception(
                "Could not persist notification event",
                extra={
                    "incident_id": str(transition.incident.id),
                    "target_id": str(target.id),
                },
            )
            return None

        return notification_event

    def _get_webhook_url(self) -> str:
        if self.settings.discord_webhook_url is None:
            raise RuntimeError("Discord webhook is not configured.")
        return self.settings.discord_webhook_url.get_secret_value()

    def _build_discord_payload(
        self,
        target: MonitoringTarget,
        check_run: CheckRun,
        transition: IncidentTransition,
    ) -> dict[str, Any]:
        incident = transition.incident
        project_name = target.project_name or "Sem projeto informado"
        provider = target.provider or "Não informado"

        if transition.event_type is NotificationEventType.INCIDENT_OPENED:
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
        total_seconds = max(0, int((end - started_at).total_seconds()))
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
