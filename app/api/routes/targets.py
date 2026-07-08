from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_api_key
from app.core.crypto import SecretConfigurationError
from app.repositories.monitoring_target_repository import MonitoringTargetRepository
from app.schemas.monitoring_target import (
    MonitoringTargetCreate,
    MonitoringTargetResponse,
    MonitoringTargetUpdate,
)

router = APIRouter(
    prefix="/api/v1/targets",
    tags=["Monitoring targets"],
    dependencies=[Depends(require_api_key)],
)


@router.post("", response_model=MonitoringTargetResponse, status_code=status.HTTP_201_CREATED)
async def create_target(
    payload: MonitoringTargetCreate,
    session: AsyncSession = Depends(get_db),
) -> MonitoringTargetResponse:
    repository = MonitoringTargetRepository(session)
    try:
        target = await repository.create(payload)
    except SecretConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    await session.commit()
    await session.refresh(target)
    return MonitoringTargetResponse.model_validate(target)


@router.get("", response_model=list[MonitoringTargetResponse])
async def list_targets(
    enabled: bool | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
) -> list[MonitoringTargetResponse]:
    repository = MonitoringTargetRepository(session)
    targets = await repository.list_all(enabled=enabled)
    return [MonitoringTargetResponse.model_validate(target) for target in targets]


@router.get("/{target_id}", response_model=MonitoringTargetResponse)
async def get_target(
    target_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> MonitoringTargetResponse:
    repository = MonitoringTargetRepository(session)
    target = await repository.get(target_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found.")
    return MonitoringTargetResponse.model_validate(target)


@router.patch("/{target_id}", response_model=MonitoringTargetResponse)
async def update_target(
    target_id: UUID,
    payload: MonitoringTargetUpdate,
    session: AsyncSession = Depends(get_db),
) -> MonitoringTargetResponse:
    repository = MonitoringTargetRepository(session)
    target = await repository.get(target_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found.")

    try:
        await repository.update(target, payload)
    except SecretConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    await session.commit()
    await session.refresh(target)
    return MonitoringTargetResponse.model_validate(target)


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(
    target_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> Response:
    repository = MonitoringTargetRepository(session)
    target = await repository.get(target_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found.")

    await repository.delete(target)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
