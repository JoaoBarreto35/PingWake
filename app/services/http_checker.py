from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter

import httpx

from app.core.config import Settings, get_settings
from app.core.crypto import SecretConfigurationError
from app.core.enums import CheckStatus
from app.core.security import UnsafeTargetError, validate_target_url_runtime
from app.db.models.monitoring_target import MonitoringTarget
from app.services.request_config_service import RequestConfigService


@dataclass(slots=True)
class HttpCheckResult:
    status: CheckStatus
    http_status_code: int | None
    latency_ms: int | None
    started_at: datetime
    finished_at: datetime
    error_type: str | None = None
    error_message: str | None = None


class HttpChecker:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.request_config = RequestConfigService(self.settings)

    async def check(self, target: MonitoringTarget) -> HttpCheckResult:
        started_at = datetime.now(UTC)
        start_counter = perf_counter()

        try:
            await validate_target_url_runtime(target.url, self.settings)
            custom_headers = self.request_config.get_headers(target)
            request_body = self.request_config.get_body(target)

            headers = {"User-Agent": f"PingWake/{self.settings.app_version}"}
            headers.update(custom_headers)
            timeout = httpx.Timeout(float(target.timeout_seconds))
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=False,
            ) as client:
                if target.has_request_body:
                    response = await client.request(
                        target.http_method.value,
                        target.url,
                        headers=headers,
                        json=request_body,
                    )
                else:
                    response = await client.request(
                        target.http_method.value,
                        target.url,
                        headers=headers,
                    )

            latency_ms = round((perf_counter() - start_counter) * 1000)
            finished_at = datetime.now(UTC)
            check_status = (
                CheckStatus.HEALTHY
                if response.status_code == target.expected_status_code
                else CheckStatus.UNHEALTHY
            )
            return HttpCheckResult(
                status=check_status,
                http_status_code=response.status_code,
                latency_ms=latency_ms,
                started_at=started_at,
                finished_at=finished_at,
                error_type=None if check_status is CheckStatus.HEALTHY else "UnexpectedStatusCode",
                error_message=(
                    None
                    if check_status is CheckStatus.HEALTHY
                    else f"Expected {target.expected_status_code}, received {response.status_code}."
                ),
            )
        except UnsafeTargetError as exc:
            return self._error_result(
                started_at,
                start_counter,
                CheckStatus.CONFIGURATION_ERROR,
                type(exc).__name__,
                str(exc),
            )
        except (SecretConfigurationError, ValueError) as exc:
            return self._error_result(
                started_at,
                start_counter,
                CheckStatus.CONFIGURATION_ERROR,
                type(exc).__name__,
                str(exc)[:500],
            )
        except httpx.TimeoutException as exc:
            return self._error_result(
                started_at,
                start_counter,
                CheckStatus.TIMEOUT,
                type(exc).__name__,
                "Target request timed out.",
            )
        except httpx.HTTPError as exc:
            return self._error_result(
                started_at,
                start_counter,
                CheckStatus.UNHEALTHY,
                type(exc).__name__,
                str(exc)[:500],
            )
        except Exception as exc:
            return self._error_result(
                started_at,
                start_counter,
                CheckStatus.UNHEALTHY,
                type(exc).__name__,
                "Unexpected error while checking target.",
            )

    @staticmethod
    def _error_result(
        started_at: datetime,
        start_counter: float,
        status: CheckStatus,
        error_type: str,
        error_message: str,
    ) -> HttpCheckResult:
        return HttpCheckResult(
            status=status,
            http_status_code=None,
            latency_ms=round((perf_counter() - start_counter) * 1000),
            started_at=started_at,
            finished_at=datetime.now(UTC),
            error_type=error_type,
            error_message=error_message,
        )
