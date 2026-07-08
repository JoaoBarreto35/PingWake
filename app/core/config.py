from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "PingWake"
    app_env: str = "development"
    app_version: str = "0.5.0"
    log_level: str = "INFO"
    docs_enabled: bool = True

    database_url: str = ""
    pingwake_api_key: SecretStr = SecretStr("development-api-key-change-me")
    pingwake_cron_key: SecretStr = SecretStr("development-cron-key-change-me")
    pingwake_encryption_key: SecretStr | None = None

    max_concurrency: int = Field(default=10, ge=1, le=100)
    default_timeout_seconds: int = Field(default=10, ge=1, le=120)
    failures_to_open_incident: int = Field(default=3, ge=1, le=20)
    successes_to_resolve_incident: int = Field(default=2, ge=1, le=20)
    default_degraded_latency_ms: int = Field(default=5000, ge=100, le=120000)
    stale_after_multiplier: float = Field(default=2.5, ge=1.1, le=20.0)
    cron_expected_interval_minutes: int = Field(default=5, ge=1, le=1440)
    cron_stale_after_multiplier: float = Field(default=3.0, ge=1.1, le=20.0)

    notifications_enabled: bool = False
    discord_webhook_url: SecretStr | None = None
    notification_timeout_seconds: int = Field(default=10, ge=1, le=60)
    notification_max_attempts: int = Field(default=4, ge=1, le=20)
    notification_retry_delays_seconds: str = "60,300,900"

    check_retention_days: int = Field(default=90, ge=1, le=3650)
    notification_retention_days: int = Field(default=365, ge=1, le=3650)
    scheduler_run_retention_days: int = Field(default=90, ge=1, le=3650)

    allow_private_targets: bool = False
    allowed_target_hosts: str = ""

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: object) -> object:
        if not isinstance(value, str) or not value.startswith("postgresql"):
            return value

        normalized = value.replace("postgresql://", "postgresql+asyncpg://", 1)
        normalized = normalized.replace("postgres://", "postgresql+asyncpg://", 1)
        parsed = urlsplit(normalized)
        query_items = []
        for key, item_value in parse_qsl(parsed.query, keep_blank_values=True):
            if key == "channel_binding":
                continue
            if key == "sslmode":
                query_items.append(("ssl", item_value))
            else:
                query_items.append((key, item_value))
        return urlunsplit(parsed._replace(query=urlencode(query_items)))

    @model_validator(mode="after")
    def validate_required_database_url(self) -> "Settings":
        if not self.database_url.strip():
            raise ValueError("DATABASE_URL is required.")
        return self

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.app_env.lower() == "production":
            forbidden = {"development-api-key-change-me", "development-cron-key-change-me"}
            if self.pingwake_api_key.get_secret_value() in forbidden:
                raise ValueError("PINGWAKE_API_KEY must be changed in production.")
            if self.pingwake_cron_key.get_secret_value() in forbidden:
                raise ValueError("PINGWAKE_CRON_KEY must be changed in production.")
        return self

    @model_validator(mode="after")
    def validate_encryption_configuration(self) -> "Settings":
        if self.pingwake_encryption_key is None:
            return self

        value = self.pingwake_encryption_key.get_secret_value().strip()
        if not value:
            self.pingwake_encryption_key = None
            return self

        try:
            from cryptography.fernet import Fernet

            Fernet(value.encode("ascii"))
        except (ValueError, UnicodeEncodeError) as exc:
            raise ValueError("PINGWAKE_ENCRYPTION_KEY must be a valid Fernet key.") from exc
        return self

    @model_validator(mode="after")
    def validate_notification_configuration(self) -> "Settings":
        if not self.notifications_enabled:
            return self

        if self.discord_webhook_url is None:
            raise ValueError("DISCORD_WEBHOOK_URL is required when NOTIFICATIONS_ENABLED is true.")

        webhook_url = self.discord_webhook_url.get_secret_value().strip()
        allowed_prefixes = (
            "https://discord.com/api/webhooks/",
            "https://discordapp.com/api/webhooks/",
        )
        if not webhook_url.startswith(allowed_prefixes):
            raise ValueError("DISCORD_WEBHOOK_URL must be a valid Discord webhook URL.")
        return self

    @property
    def notification_retry_delays(self) -> tuple[int, ...]:
        values: list[int] = []
        for raw_value in self.notification_retry_delays_seconds.split(","):
            raw_value = raw_value.strip()
            if not raw_value:
                continue
            try:
                value = int(raw_value)
            except ValueError as exc:
                raise ValueError(
                    "NOTIFICATION_RETRY_DELAYS_SECONDS must contain integers separated by commas."
                ) from exc
            if value < 1 or value > 86400:
                raise ValueError(
                    "Each notification retry delay must be between 1 and 86400 seconds."
                )
            values.append(value)
        return tuple(values) or (60,)

    @property
    def allowed_hosts(self) -> set[str]:
        return {
            host.strip().lower() for host in self.allowed_target_hosts.split(",") if host.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
