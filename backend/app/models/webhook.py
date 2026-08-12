import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import WebhookDeliveryStatus
from app.models.types import GUID, JSONType

if TYPE_CHECKING:
    from app.models.user import User


class Webhook(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A user-configured HTTP callback subscribed to one or more events (spec section 22)."""

    __tablename__ = "webhooks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Signing secret — kept in plaintext because it must be reused to sign
    # every outgoing delivery (unlike a login credential, it is never
    # verified by hashing; it is HMAC key material). Never returned in full
    # by the list endpoint after creation, only at creation/rotation time.
    secret: Mapped[str] = mapped_column(String(128), nullable=False)
    events: Mapped[list[str]] = mapped_column(JSONType, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    owner: Mapped["User"] = relationship(back_populates="webhooks")
    deliveries: Mapped[list["WebhookDelivery"]] = relationship(
        back_populates="webhook", cascade="all, delete-orphan"
    )


class WebhookDelivery(UUIDPrimaryKeyMixin, Base):
    """One attempted (and possibly retried) delivery of an event to a Webhook."""

    __tablename__ = "webhook_deliveries"

    webhook_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("webhooks.id", ondelete="CASCADE"), index=True, nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONType, nullable=False)
    status: Mapped[WebhookDeliveryStatus] = mapped_column(
        String(10), default=WebhookDeliveryStatus.PENDING, nullable=False
    )
    response_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )

    webhook: Mapped["Webhook"] = relationship(back_populates="deliveries")
