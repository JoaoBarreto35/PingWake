from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.core.config import get_settings
from app.core.enums import (
    CheckStatus,
    Environment,
    HttpMethod,
    MonitoringMode,
    TargetType,
)
from app.core.security import UnsafeTargetError, validate_target_url_static


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
    pass


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
    enabled: bool | None = None

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


class MonitoringTargetResponse(MonitoringTargetBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    last_status: CheckStatus
    last_checked_at: datetime | None
    next_check_at: datetime
    consecutive_failures: int
    consecutive_successes: int
    created_at: datetime
    updated_at: datetime
