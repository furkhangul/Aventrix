from pydantic import BaseModel

from app.schemas.dashboard import TimeseriesPoint, TopItem


class AnalyticsOverview(BaseModel):
    total_visits: int
    unique_visitors: int
    conversion_rate: float
    timeseries: list[TimeseriesPoint]
    top_countries: list[TopItem]
    top_devices: list[TopItem]
    top_browsers: list[TopItem]
    top_os: list[TopItem]
    top_referrers: list[TopItem]
