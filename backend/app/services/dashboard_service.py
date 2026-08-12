import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign
from app.models.enums import CampaignStatus
from app.models.link import Link
from app.models.visit import Visit
from app.schemas.dashboard import DashboardSummary, TimeseriesPoint, TopItem


def _today_start(now: datetime | None = None) -> datetime:
    now = now or datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


async def get_summary(
    db: AsyncSession, *, user_id: uuid.UUID, date_from: datetime, date_to: datetime
) -> DashboardSummary:
    total_links = (
        await db.execute(select(func.count()).select_from(Link).where(Link.user_id == user_id))
    ).scalar_one()

    active_campaigns = (
        await db.execute(
            select(func.count())
            .select_from(Campaign)
            .where(Campaign.user_id == user_id, Campaign.status == CampaignStatus.ACTIVE)
        )
    ).scalar_one()

    total_visits = (
        await db.execute(
            select(func.count())
            .select_from(Visit)
            .join(Link, Visit.link_id == Link.id)
            .where(Link.user_id == user_id, Visit.created_at.between(date_from, date_to))
        )
    ).scalar_one()

    unique_visitors = (
        await db.execute(
            select(func.count(func.distinct(Visit.visitor_hash)))
            .select_from(Visit)
            .join(Link, Visit.link_id == Link.id)
            .where(
                Link.user_id == user_id,
                Visit.visitor_hash.is_not(None),
                Visit.created_at.between(date_from, date_to),
            )
        )
    ).scalar_one()

    today_start = _today_start()
    today_visits = (
        await db.execute(
            select(func.count())
            .select_from(Visit)
            .join(Link, Visit.link_id == Link.id)
            .where(Link.user_id == user_id, Visit.created_at >= today_start)
        )
    ).scalar_one()

    conversion_rate = round((unique_visitors / total_visits) * 100, 2) if total_visits else 0.0

    return DashboardSummary(
        total_links=total_links,
        total_visits=total_visits,
        unique_visitors=unique_visitors,
        today_visits=today_visits,
        active_campaigns=active_campaigns,
        conversion_rate=conversion_rate,
    )


_TOP_DIMENSION_COLUMNS = {
    "country": Visit.country,
    "device": Visit.device_type,
    "browser": Visit.browser,
    "referrer": Visit.referrer,
    "os": Visit.os,
}


async def get_top_dimension(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    dimension: str,
    date_from: datetime,
    date_to: datetime,
    limit: int = 5,
) -> list[TopItem]:
    column = _TOP_DIMENSION_COLUMNS.get(dimension)
    if column is None:
        raise ValueError(f"Unknown dashboard dimension: {dimension}")

    stmt = (
        select(column.label("label"), func.count().label("count"))
        .select_from(Visit)
        .join(Link, Visit.link_id == Link.id)
        .where(
            Link.user_id == user_id,
            column.is_not(None),
            Visit.created_at.between(date_from, date_to),
        )
        .group_by(column)
        .order_by(func.count().desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).all()
    return [TopItem(label=row.label, count=row.count) for row in rows]


async def get_visits_timeseries(
    db: AsyncSession, *, user_id: uuid.UUID, date_from: datetime, date_to: datetime
) -> list[TimeseriesPoint]:
    # Bucketed in Python rather than SQL (DATE_TRUNC/date() aren't portable
    # across Postgres and SQLite) — fine at this scale, and keeps the exact
    # same code path testable without a live Postgres.
    stmt = (
        select(Visit.created_at)
        .select_from(Visit)
        .join(Link, Visit.link_id == Link.id)
        .where(Link.user_id == user_id, Visit.created_at.between(date_from, date_to))
    )
    timestamps = (await db.execute(stmt)).scalars().all()

    counts_by_day: Counter = Counter()
    for ts in timestamps:
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        counts_by_day[ts.date()] += 1

    points: list[TimeseriesPoint] = []
    cursor = date_from.date()
    end_date = date_to.date()
    while cursor <= end_date:
        points.append(TimeseriesPoint(date=cursor, count=counts_by_day.get(cursor, 0)))
        cursor += timedelta(days=1)
    return points
