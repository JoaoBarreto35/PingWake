from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_api_key
from app.core.enums import NotificationEventType, NotificationStatus
from app.repositories.notification_event_repository import NotificationEventRepository
from app.schemas.notification import NotificationEventResponse
from app.services.notification_service import NotificationService

router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["Notifications"],
    dependencies=[Depends(require_api_key)],
)


@router.get("", response_model=list[NotificationEventResponse])
async def list_notification_events(
    target_id: UUID | None = Query(default=None),
    event_type: NotificationEventType | None = Query(default=None),
    notification_status: NotificationStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
) -> list[NotificationEventResponse]:
    repository = NotificationEventRepository(session)
    events = await repository.list_all(
        target_id=target_id,
        event_type=event_type,
        status_filter=notification_status,
        limit=limit,
    )
    return [NotificationEventResponse.model_validate(event) for event in events]


@router.post("/{notification_id}/retry", response_model=NotificationEventResponse)
async def retry_notification(
    notification_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> NotificationEventResponse:
    event = await NotificationService().retry_event(session, notification_id, force=True)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification event not found.",
        )
    return NotificationEventResponse.model_validate(event)
