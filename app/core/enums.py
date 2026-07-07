from enum import StrEnum


class TargetType(StrEnum):
    API = "api"
    DATABASE = "database"
    WEBSITE = "website"
    WEBHOOK = "webhook"


class MonitoringMode(StrEnum):
    MONITOR = "monitor"
    KEEP_AWAKE = "keep_awake"
    DATABASE_ACTIVITY = "database_activity"


class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class HttpMethod(StrEnum):
    GET = "GET"
    HEAD = "HEAD"


class CheckStatus(StrEnum):
    PENDING = "pending"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    TIMEOUT = "timeout"
    CONFIGURATION_ERROR = "configuration_error"


class IncidentStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
