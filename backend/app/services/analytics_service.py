import csv
import io
import json
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link
from app.models.visit import Visit
from app.repositories.campaign_repository import get_owned_campaign
from app.repositories.link_repository import get_owned_link
from app.schemas.analytics import AnalyticsOverview
from app.schemas.dashboard import TimeseriesPoint, TopItem
from app.services.exceptions import NotFoundError

_DIMENSION_COLUMNS = {
    "country": Visit.country,
    "device": Visit.device_type,
    "browser": Visit.browser,
    "os": Visit.os,
    "referrer": Visit.referrer,
}


async def _validate_filters(
    db: AsyncSession, *, user_id: uuid.UUID, link_id: uuid.UUID | None, campaign_id: uuid.UUID | None
) -> None:
    """IDOR guard: a link_id/campaign_id filter must belong to the requesting user."""
    if link_id is not None and not await get_owned_link(db, user_id=user_id, link_id=link_id):
        raise NotFoundError("Link not found")
    if campaign_id is not None and not await get_owned_campaign(db, user_id=user_id, campaign_id=campaign_id):
        raise NotFoundError("Campaign not found")


def _scope(stmt, *, user_id: uuid.UUID, date_from: datetime, date_to: datetime, link_id, campaign_id):
    stmt = (
        stmt.select_from(Visit)
        .join(Link, Visit.link_id == Link.id)
        .where(Link.user_id == user_id, Visit.created_at.between(date_from, date_to))
    )
    if link_id is not None:
        stmt = stmt.where(Visit.link_id == link_id)
    if campaign_id is not None:
        stmt = stmt.where(Visit.campaign_id == campaign_id)
    return stmt


async def get_overview(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    date_from: datetime,
    date_to: datetime,
    link_id: uuid.UUID | None = None,
    campaign_id: uuid.UUID | None = None,
) -> AnalyticsOverview:
    await _validate_filters(db, user_id=user_id, link_id=link_id, campaign_id=campaign_id)

    def scoped(stmt):
        return _scope(stmt, user_id=user_id, date_from=date_from, date_to=date_to, link_id=link_id, campaign_id=campaign_id)

    total_visits = (await db.execute(scoped(select(func.count())))).scalar_one()
    unique_visitors = (
        await db.execute(
            scoped(select(func.count(func.distinct(Visit.visitor_hash)))).where(Visit.visitor_hash.is_not(None))
        )
    ).scalar_one()
    conversion_rate = round((unique_visitors / total_visits) * 100, 2) if total_visits else 0.0

    timestamps = (await db.execute(scoped(select(Visit.created_at)))).scalars().all()
    counts_by_day: Counter = Counter()
    for ts in timestamps:
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        counts_by_day[ts.date()] += 1
    timeseries: list[TimeseriesPoint] = []
    cursor = date_from.date()
    end_date = date_to.date()
    while cursor <= end_date:
        timeseries.append(TimeseriesPoint(date=cursor, count=counts_by_day.get(cursor, 0)))
        cursor += timedelta(days=1)

    tops: dict[str, list[TopItem]] = {}
    for key, column in _DIMENSION_COLUMNS.items():
        stmt = (
            scoped(select(column.label("label"), func.count().label("count")))
            .where(column.is_not(None))
            .group_by(column)
            .order_by(func.count().desc())
            .limit(5)
        )
        rows = (await db.execute(stmt)).all()
        tops[key] = [TopItem(label=row.label, count=row.count) for row in rows]

    return AnalyticsOverview(
        total_visits=total_visits,
        unique_visitors=unique_visitors,
        conversion_rate=conversion_rate,
        timeseries=timeseries,
        top_countries=tops["country"],
        top_devices=tops["device"],
        top_browsers=tops["browser"],
        top_os=tops["os"],
        top_referrers=tops["referrer"],
    )


async def export_report(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    date_from: datetime,
    date_to: datetime,
    link_id: uuid.UUID | None = None,
    campaign_id: uuid.UUID | None = None,
    format: str = "csv",
) -> tuple[bytes, str, str]:
    overview = await get_overview(
        db, user_id=user_id, date_from=date_from, date_to=date_to, link_id=link_id, campaign_id=campaign_id
    )

    report = {
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "total_visits": overview.total_visits,
        "unique_visitors": overview.unique_visitors,
        "conversion_rate": overview.conversion_rate,
        "top_countries": [t.model_dump() for t in overview.top_countries],
        "top_devices": [t.model_dump() for t in overview.top_devices],
        "top_browsers": [t.model_dump() for t in overview.top_browsers],
        "top_os": [t.model_dump() for t in overview.top_os],
        "top_referrers": [t.model_dump() for t in overview.top_referrers],
    }

    if format == "json":
        return json.dumps(report, indent=2).encode("utf-8"), "application/json", "analytics-report.json"

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Date from", report["date_from"]])
    writer.writerow(["Date to", report["date_to"]])
    writer.writerow(["Total visits", report["total_visits"]])
    writer.writerow(["Unique visitors", report["unique_visitors"]])
    writer.writerow(["Conversion rate (%)", report["conversion_rate"]])
    for dimension in ("top_countries", "top_devices", "top_browsers", "top_os", "top_referrers"):
        writer.writerow([])
        writer.writerow([dimension.replace("_", " ").title()])
        writer.writerow(["Label", "Count"])
        for item in report[dimension]:
            writer.writerow([item["label"], item["count"]])

    return buffer.getvalue().encode("utf-8"), "text/csv", "analytics-report.csv"
