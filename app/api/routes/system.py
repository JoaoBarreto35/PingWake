from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_api_key
from app.schemas.system import ReliabilitySummaryResponse
from app.services.system_status_service import SystemStatusService

router = APIRouter(
    prefix="/api/v1/system",
    tags=["System reliability"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/status", response_model=ReliabilitySummaryResponse)
async def get_system_status(
    session: AsyncSession = Depends(get_db),
) -> ReliabilitySummaryResponse:
    return await SystemStatusService().build(session)
