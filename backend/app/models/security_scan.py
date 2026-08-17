import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin
from app.models.types import GUID, JSONType

if TYPE_CHECKING:
    from app.models.user import User


class SecurityScan(UUIDPrimaryKeyMixin, Base):
    """A single Security Center run against a domain (spec section 19/20/44/45)."""

    __tablename__ = "security_scans"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    domain: Mapped[str] = mapped_column(String(255), index=True, nullable=False)

    score: Mapped[int] = mapped_column(Integer, nullable=False)

    ssl_info: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    dns_records: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    whois_info: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    headers_info: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    reputation_info: Mapped[dict | None] = mapped_column(JSONType, nullable=True)

    # Recon / OSINT extensions (spec: subdomains, IP/ASN, cookies, tech
    # fingerprint, robots/sitemap, DNS propagation, aggregated findings).
    ip_info: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    subdomains: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    dns_propagation: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    cookie_info: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    tech_info: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    robots_info: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    findings: Mapped[list | None] = mapped_column(JSONType, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="security_scans")
