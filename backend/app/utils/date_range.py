from datetime import datetime, time, timedelta, timezone
from enum import Enum


class DateRangePreset(str, Enum):
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    LAST_90_DAYS = "90d"
    CUSTOM = "custom"


def _start_of_day(dt: datetime) -> datetime:
    return datetime.combine(dt.date(), time.min, tzinfo=timezone.utc)


def resolve_date_range(
    preset: DateRangePreset,
    custom_start: datetime | None = None,
    custom_end: datetime | None = None,
) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    today_start = _start_of_day(now)

    if preset == DateRangePreset.TODAY:
        return today_start, now
    if preset == DateRangePreset.YESTERDAY:
        yesterday_start = today_start - timedelta(days=1)
        return yesterday_start, today_start
    if preset == DateRangePreset.LAST_7_DAYS:
        return today_start - timedelta(days=6), now
    if preset == DateRangePreset.LAST_30_DAYS:
        return today_start - timedelta(days=29), now
    if preset == DateRangePreset.LAST_90_DAYS:
        return today_start - timedelta(days=89), now
    if preset == DateRangePreset.CUSTOM:
        if not custom_start or not custom_end:
            raise ValueError("custom_start and custom_end are required for a custom range")
        return custom_start, custom_end
    raise ValueError(f"Unknown date range preset: {preset}")
