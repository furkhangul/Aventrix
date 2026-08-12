import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import CampaignStatus
from app.models.types import GUID, JSONType

if TYPE_CHECKING:
    from app.models.link import Link
    from app.models.user import User


class Campaign(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "campaigns"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    status: Mapped[CampaignStatus] = mapped_column(
        String(20), default=CampaignStatus.ACTIVE, nullable=False
    )
    tags: Mapped[list[str] | None] = mapped_column(JSONType, nullable=True)

    owner: Mapped["User"] = relationship(back_populates="campaigns")
    # passive_deletes: rely on the FK's ON DELETE SET NULL (see Link.campaign_id)
    # rather than SQLAlchemy issuing per-row UPDATE/DELETE statements itself.
    links: Mapped[list["Link"]] = relationship(back_populates="campaign", passive_deletes=True)
