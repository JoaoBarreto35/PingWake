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
    app_version: str = "0.3.0"
    log_level: str = "INFO"
    docs_enabled: bool = True

    database_url: str = ""
    pingwake_api_key: SecretStr = SecretStr("development-api-key-change-me")
    pingwake_cron_key: SecretStr = SecretStr("development-cron-key-change-me")

    max_concurrency: int = Field(default=10, ge=1, le=100)
    default_timeout_seconds: int = Field(default=10, ge=1, le=120)
    failures_to_open_incident: int = Field(default=3, ge=1, le=20)
    successes_to_resolve_incident: int = Field(default=2, ge=1, le=20)

    notifications_enabled: bool = False
    discord_webhook_url: SecretStr | None = None
    notification_timeout_seconds: int = Field(default=10, ge=1, le=60)

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
    def validate_notification_configuration(self) -> "Settings":
        if not self.notifications_enabled:
            return self

        if self.discord_webhook_url is None:
            raise ValueError(
                "DISCORD_WEBHOOK_URL is required when NOTIFICATIONS_ENABLED is true."
            )

        webhook_url = self.discord_webhook_url.get_secret_value().strip()
        allowed_prefixes = (
            "https://discord.com/api/webhooks/",
            "https://discordapp.com/api/webhooks/",
        )
        if not webhook_url.startswith(allowed_prefixes):
            raise ValueError("DISCORD_WEBHOOK_URL must be a valid Discord webhook URL.")
        return self

    @property
    def allowed_hosts(self) -> set[str]:
        return {
            host.strip().lower() for host in self.allowed_target_hosts.split(",") if host.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
