from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardSummary, TimeseriesPoint, TopItem
from app.services import dashboard_service
from app.utils.date_range import DateRangePreset, resolve_date_range

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _resolve_range(range_: DateRangePreset, start: datetime | None, end: datetime | None):
    try:
        return resolve_date_range(range_, custom_start=start, custom_end=end)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/summary", response_model=DashboardSummary)
async def get_summary(
    range: DateRangePreset = DateRangePreset.LAST_30_DAYS,
    start: datetime | None = None,
    end: datetime | None = None,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    date_from, date_to = _resolve_range(range, start, end)
    return await dashboard_service.get_summary(db, user_id=user.id, date_from=date_from, date_to=date_to)


@router.get("/timeseries", response_model=list[TimeseriesPoint])
async def get_timeseries(
    range: DateRangePreset = DateRangePreset.LAST_30_DAYS,
    start: datetime | None = None,
    end: datetime | None = None,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    date_from, date_to = _resolve_range(range, start, end)
    return await dashboard_service.get_visits_timeseries(db, user_id=user.id, date_from=date_from, date_to=date_to)


@router.get("/top/{dimension}", response_model=list[TopItem])
async def get_top(
    dimension: str,
    range: DateRangePreset = DateRangePreset.LAST_30_DAYS,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = Query(default=5, ge=1, le=20),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    date_from, date_to = _resolve_range(range, start, end)
    try:
        return await dashboard_service.get_top_dimension(
            db, user_id=user.id, dimension=dimension, date_from=date_from, date_to=date_to, limit=limit
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
