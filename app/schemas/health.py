from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime
    dependencies: dict[str, str] = Field(default_factory=dict)
