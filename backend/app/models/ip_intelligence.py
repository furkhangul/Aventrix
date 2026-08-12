from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import TriState


class IPIntelligenceCache(Base, UUIDPrimaryKeyMixin):
    """
    Cache of provider lookups, keyed by a salted hash of the IP (never the
    raw IP itself) so we don't re-query the provider on every click and
    never persist a reversible IP address. Rows expire per DATA_RETENTION
    settings; see docs/DATABASE.md.
    """

    __tablename__ = "ip_intelligence"

    ip_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    isp: Mapped[str | None] = mapped_column(String(255), nullable=True)
    asn: Mapped[str | None] = mapped_column(String(32), nullable=True)
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_mobile: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    is_vpn: Mapped[TriState] = mapped_column(String(10), default=TriState.UNKNOWN, nullable=False)
    is_proxy: Mapped[TriState] = mapped_column(String(10), default=TriState.UNKNOWN, nullable=False)
    is_tor: Mapped[TriState] = mapped_column(String(10), default=TriState.UNKNOWN, nullable=False)
    is_hosting: Mapped[TriState] = mapped_column(String(10), default=TriState.UNKNOWN, nullable=False)

    provider: Mapped[str] = mapped_column(String(50), nullable=False)

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
