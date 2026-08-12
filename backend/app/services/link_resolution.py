import enum
from datetime import datetime, timezone

from app.core.security import verify_password
from app.models.enums import CampaignStatus
from app.models.link import Link


class LinkGateReason(str, enum.Enum):
    NOT_FOUND = "NOT_FOUND"
    EXPIRED = "EXPIRED"
    DISABLED = "DISABLED"
    CAMPAIGN_PAUSED = "CAMPAIGN_PAUSED"
    CAMPAIGN_ARCHIVED = "CAMPAIGN_ARCHIVED"


def is_link_usable(link: Link | None) -> tuple[bool, LinkGateReason | None]:
    """
    Callers must have eagerly loaded `link.campaign` (see
    `selectinload(Link.campaign)` in `get_link_by_short_code`) — accessing
    an unloaded relationship here would raise on the async session.
    """
    if link is None:
        return False, LinkGateReason.NOT_FOUND
    if not link.is_active:
        return False, LinkGateReason.DISABLED
    if link.expires_at is not None:
        expires_at = link.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            return False, LinkGateReason.EXPIRED
    # A campaign's status is a real switch, not just a label: pausing or
    # archiving a campaign takes every one of its links offline too, so
    # "Pause" actually does something.
    if link.campaign is not None:
        if link.campaign.status == CampaignStatus.PAUSED:
            return False, LinkGateReason.CAMPAIGN_PAUSED
        if link.campaign.status == CampaignStatus.ARCHIVED:
            return False, LinkGateReason.CAMPAIGN_ARCHIVED
    return True, None


def check_link_password(link: Link, password: str | None) -> bool:
    if not link.is_password_protected:
        return True
    if not password or not link.password_hash:
        return False
    return verify_password(password, link.password_hash)
