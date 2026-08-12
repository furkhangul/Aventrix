import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.analytics import AnalyticsOverview
from app.services import analytics_service
from app.services.exceptions import NotFoundError
from app.utils.date_range import DateRangePreset, resolve_date_range

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _resolve_range(range_: DateRangePreset, start: datetime | None, end: datetime | None):
    try:
        return resolve_date_range(range_, custom_start=start, custom_end=end)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/overview", response_model=AnalyticsOverview)
async def get_overview(
    range: DateRangePreset = DateRangePreset.LAST_30_DAYS,
    start: datetime | None = None,
    end: datetime | None = None,
    link_id: uuid.UUID | None = None,
    campaign_id: uuid.UUID | None = None,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    date_from, date_to = _resolve_range(range, start, end)
    try:
        return await analytics_service.get_overview(
            db,
            user_id=user.id,
            date_from=date_from,
            date_to=date_to,
            link_id=link_id,
            campaign_id=campaign_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc) or "Not found")


@router.get("/export")
async def export_report(
    range: DateRangePreset = DateRangePreset.LAST_30_DAYS,
    start: datetime | None = None,
    end: datetime | None = None,
    link_id: uuid.UUID | None = None,
    campaign_id: uuid.UUID | None = None,
    format: str = "csv",
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if format not in ("csv", "json"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="format must be 'csv' or 'json'")
    date_from, date_to = _resolve_range(range, start, end)
    try:
        content, content_type, filename = await analytics_service.export_report(
            db,
            user_id=user.id,
            date_from=date_from,
            date_to=date_to,
            link_id=link_id,
            campaign_id=campaign_id,
            format=format,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc) or "Not found")

    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
