from fastapi import APIRouter, Depends

from app.api.dependencies import require_cron_key
from app.schemas.check_run import BatchCheckResponse
from app.services.check_runner import CheckRunner

router = APIRouter(
    prefix="/internal/checks",
    tags=["Internal"],
    dependencies=[Depends(require_cron_key)],
)


@router.post("/run-due", response_model=BatchCheckResponse)
async def run_due_checks() -> BatchCheckResponse:
    runner = CheckRunner()
    result = await runner.run_due_targets()
    return BatchCheckResponse(**result)
