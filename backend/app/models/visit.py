import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import TriState
from app.models.types import GUID, JSONType

if TYPE_CHECKING:
    from app.models.link import Link


class Visit(UUIDPrimaryKeyMixin, Base):
    """
    A single click/visit on a tracking link.
    """

    __tablename__ = "visits"

    link_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("links.id", ondelete="CASCADE"), index=True, nullable=False
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("campaigns.id", ondelete="SET NULL"), index=True, nullable=True
    )

    consent_given: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Salted hash of IP (+ link) used for unique-visitor counting.
    visitor_hash: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    # Raw client IP (IPv4 or IPv6), stored for every visit regardless of consent.
    ip_address: Mapped[str | None] = mapped_column(String(45), index=True, nullable=True)

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
    # Reverse-DNS (PTR) hostname for the IP, e.g. "123.45.67.89.example-isp.net".
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Whether the ISP/ASN is a mobile carrier (from provider data, not a live device signal).
    is_mobile: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    is_vpn: Mapped[TriState] = mapped_column(String(10), default=TriState.UNKNOWN, nullable=False)
    is_proxy: Mapped[TriState] = mapped_column(String(10), default=TriState.UNKNOWN, nullable=False)
    is_tor: Mapped[TriState] = mapped_column(String(10), default=TriState.UNKNOWN, nullable=False)
    is_hosting: Mapped[TriState] = mapped_column(String(10), default=TriState.UNKNOWN, nullable=False)

    browser: Mapped[str | None] = mapped_column(String(100), nullable=True)
    browser_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    os: Mapped[str | None] = mapped_column(String(100), nullable=True)
    os_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    language: Mapped[str | None] = mapped_column(String(20), nullable=True)
    referrer: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Bot-detection confidence, per spec section 76 (not a hard classification).
    bot_confidence: Mapped[str] = mapped_column(String(20), default="UNKNOWN", nullable=False)

    utm_snapshot: Mapped[dict | None] = mapped_column(JSONType, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )

    link: Mapped["Link"] = relationship(back_populates="visits")
