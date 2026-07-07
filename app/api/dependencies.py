from collections.abc import AsyncIterator

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_session

api_key_header = APIKeyHeader(name="X-PingWake-Key", auto_error=False)
cron_key_header = APIKeyHeader(name="X-PingWake-Cron-Key", auto_error=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async for session in get_session():
        yield session


def require_api_key(
    supplied_key: str | None = Depends(api_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    expected = settings.pingwake_api_key.get_secret_value()
    if supplied_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )


def require_cron_key(
    supplied_key: str | None = Depends(cron_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    expected = settings.pingwake_cron_key.get_secret_value()
    if supplied_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Cron key.",
        )
