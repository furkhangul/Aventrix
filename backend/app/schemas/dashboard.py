from datetime import date

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_links: int
    total_visits: int
    unique_visitors: int
    today_visits: int
    active_campaigns: int
    conversion_rate: float  # unique_visitors / total_visits * 100, within the selected range


class TopItem(BaseModel):
    label: str
    count: int


class TimeseriesPoint(BaseModel):
    date: date
    count: int
