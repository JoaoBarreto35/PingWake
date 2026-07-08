import json
import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, JsonValue, field_validator

from app.core.config import get_settings
from app.core.enums import (
    CheckStatus,
    Environment,
    HttpMethod,
    MonitoringMode,
    TargetType,
)
from app.core.security import UnsafeTargetError, validate_target_url_static

_HEADER_NAME_PATTERN = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
_FORBIDDEN_HEADER_NAMES = {
    "connection",
    "content-length",
    "host",
    "proxy-connection",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}
_MAX_HEADER_COUNT = 30
_MAX_HEADER_VALUE_LENGTH = 4096
_MAX_HEADERS_SERIALIZED_BYTES = 16_384
_MAX_BODY_SERIALIZED_BYTES = 65_536


def _validate_request_headers(value: dict[str, str] | None) -> dict[str, str] | None:
    if value is None:
        return None
    if len(value) > _MAX_HEADER_COUNT:
        raise ValueError(f"At most {_MAX_HEADER_COUNT} custom headers are allowed.")

    normalized: dict[str, str] = {}
    for raw_name, raw_value in value.items():
        name = raw_name.strip()
        if not name or not _HEADER_NAME_PATTERN.fullmatch(name):
            raise ValueError(f"Invalid HTTP header name: {raw_name!r}.")
        if name.lower() in _FORBIDDEN_HEADER_NAMES:
            raise ValueError(f"Header {name!r} is managed by the HTTP client and cannot be set.")
        if "\r" in raw_value or "\n" in raw_value:
            raise ValueError(f"Header {name!r} contains an invalid line break.")
        if len(raw_value) > _MAX_HEADER_VALUE_LENGTH:
            raise ValueError(f"Header {name!r} is too long.")
        normalized[name] = raw_value

    serialized = json.dumps(normalized, ensure_ascii=False).encode("utf-8")
    if len(serialized) > _MAX_HEADERS_SERIALIZED_BYTES:
        raise ValueError("Custom headers exceed the 16 KB limit.")
    return normalized


def _validate_request_body(value: JsonValue | None) -> JsonValue | None:
    if value is None:
        return None
    serialized = json.dumps(value, ensure_ascii=False).encode("utf-8")
    if len(serialized) > _MAX_BODY_SERIALIZED_BYTES:
        raise ValueError("Request body exceeds the 64 KB limit.")
    return value


class MonitoringTargetBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    project_name: str | None = Field(default=None, max_length=120)
    devbase_project_id: str | None = Field(default=None, max_length=120)
    target_type: TargetType = TargetType.API
    monitoring_mode: MonitoringMode = MonitoringMode.MONITOR
    environment: Environment = Environment.PRODUCTION
    provider: str | None = Field(default=None, max_length=80)
    url: HttpUrl
    http_method: HttpMethod = HttpMethod.GET
    expected_status_code: int = Field(default=200, ge=100, le=599)
    interval_minutes: int = Field(default=30, ge=1, le=10080)
    timeout_seconds: int = Field(default=10, ge=1, le=120)
    degraded_latency_ms: int | None = Field(default=None, ge=100, le=120000)
    failure_threshold: int | None = Field(default=None, ge=1, le=20)
    recovery_threshold: int | None = Field(default=None, ge=1, le=20)
    enabled: bool = True

    @field_validator("url")
    @classmethod
    def validate_url_security(cls, value: HttpUrl) -> HttpUrl:
        try:
            validate_target_url_static(str(value), get_settings())
        except UnsafeTargetError as exc:
            raise ValueError(str(exc)) from exc
        return value


class MonitoringTargetCreate(MonitoringTargetBase):
    request_headers: dict[str, str] | None = Field(
        default=None,
        description=(
            "Optional HTTP headers. Values are encrypted before storage and are never returned "
            "by the API."
        ),
        json_schema_extra={"writeOnly": True},
    )
    request_body: JsonValue | None = Field(
        default=None,
        description=(
            "Optional JSON body. It is encrypted before storage and is never returned by the API."
        ),
        json_schema_extra={"writeOnly": True},
    )

    _validate_headers = field_validator("request_headers")(_validate_request_headers)
    _validate_body = field_validator("request_body")(_validate_request_body)


class MonitoringTargetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    project_name: str | None = Field(default=None, max_length=120)
    devbase_project_id: str | None = Field(default=None, max_length=120)
    target_type: TargetType | None = None
    monitoring_mode: MonitoringMode | None = None
    environment: Environment | None = None
    provider: str | None = Field(default=None, max_length=80)
    url: HttpUrl | None = None
    http_method: HttpMethod | None = None
    expected_status_code: int | None = Field(default=None, ge=100, le=599)
    interval_minutes: int | None = Field(default=None, ge=1, le=10080)
    timeout_seconds: int | None = Field(default=None, ge=1, le=120)
    degraded_latency_ms: int | None = Field(default=None, ge=100, le=120000)
    failure_threshold: int | None = Field(default=None, ge=1, le=20)
    recovery_threshold: int | None = Field(default=None, ge=1, le=20)
    enabled: bool | None = None
    request_headers: dict[str, str] | None = Field(
        default=None,
        description=(
            "Omit to preserve the encrypted headers, send null or an empty object to clear them."
        ),
        json_schema_extra={"writeOnly": True},
    )
    request_body: JsonValue | None = Field(
        default=None,
        description="Omit to preserve the encrypted body, send null to clear it.",
        json_schema_extra={"writeOnly": True},
    )

    @field_validator("url")
    @classmethod
    def validate_url_security(cls, value: HttpUrl | None) -> HttpUrl | None:
        if value is None:
            return None
        try:
            validate_target_url_static(str(value), get_settings())
        except UnsafeTargetError as exc:
            raise ValueError(str(exc)) from exc
        return value

    _validate_headers = field_validator("request_headers")(_validate_request_headers)
    _validate_body = field_validator("request_body")(_validate_request_body)


class MonitoringTargetResponse(MonitoringTargetBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    has_custom_headers: bool
    has_request_body: bool
    last_status: CheckStatus
    last_checked_at: datetime | None
    next_check_at: datetime
    consecutive_failures: int
    consecutive_successes: int
    created_at: datetime
    updated_at: datetime
