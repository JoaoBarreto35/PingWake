from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_api_key
from app.repositories.check_run_repository import CheckRunRepository
from app.repositories.monitoring_target_repository import MonitoringTargetRepository
from app.schemas.check_run import CheckRunResponse
from app.services.check_runner import CheckRunner

router = APIRouter(
    prefix="/api/v1/targets",
    tags=["Checks"],
    dependencies=[Depends(require_api_key)],
)


@router.post("/{target_id}/check", response_model=CheckRunResponse)
async def run_target_check(
    target_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> CheckRunResponse:
    target_repository = MonitoringTargetRepository(session)
    target = await target_repository.get(target_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found.")

    runner = CheckRunner()
    check_run = await runner.run_target(session, target, trigger_source="manual")
    return CheckRunResponse.model_validate(check_run)


@router.get("/{target_id}/checks", response_model=list[CheckRunResponse])
async def list_target_checks(
    target_id: UUID,
    limit: int = Query(default=50, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
) -> list[CheckRunResponse]:
    target_repository = MonitoringTargetRepository(session)
    if await target_repository.get(target_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found.")

    check_repository = CheckRunRepository(session)
    checks = await check_repository.list_by_target(target_id, limit=limit)
    return [CheckRunResponse.model_validate(check) for check in checks]
