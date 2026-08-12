import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.types import GUID, JSONType

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.user import User
    from app.models.visit import Visit


class Link(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "links"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # SET NULL (not CASCADE): deleting a campaign un-links its links rather
    # than deleting them — losing a link (and its whole visit history) as a
    # side effect of tidying up a campaign would be a surprising, unrecoverable
    # data-loss trap.
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    short_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSONType, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Set once the expiry-sweep worker has sent a LINK_EXPIRED notification,
    # so the same expiration is never notified twice.
    expiry_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_password_protected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Whether visitors must explicitly consent before technical data is collected.
    requires_consent: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    utm_params: Mapped[dict | None] = mapped_column(JSONType, nullable=True)

    owner: Mapped["User"] = relationship(back_populates="links")
    campaign: Mapped["Campaign | None"] = relationship(back_populates="links")
    visits: Mapped[list["Visit"]] = relationship(
        back_populates="link", cascade="all, delete-orphan"
    )
