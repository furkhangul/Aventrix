import enum


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    USER = "USER"
    VIEWER = "VIEWER"


# Ordering used for "at least this role" checks. Higher index = more privilege.
ROLE_HIERARCHY = [
    UserRole.VIEWER,
    UserRole.USER,
    UserRole.MANAGER,
    UserRole.ADMIN,
    UserRole.SUPER_ADMIN,
]


class CampaignStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"


class TriState(str, enum.Enum):
    """For security signals where certainty isn't always available."""

    YES = "YES"
    NO = "NO"
    UNKNOWN = "UNKNOWN"


class AuditResult(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class ApiKeyTier(str, enum.Enum):
    FREE = "FREE"
    PRO = "PRO"
    BUSINESS = "BUSINESS"


class WebhookEventType(str, enum.Enum):
    LINK_CREATED = "link.created"
    LINK_CLICKED = "link.clicked"
    CAMPAIGN_CREATED = "campaign.created"
    CAMPAIGN_COMPLETED = "campaign.completed"
    SECURITY_ALERT = "security.alert"


class WebhookDeliveryStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class NotificationType(str, enum.Enum):
    LINK_EXPIRED = "LINK_EXPIRED"
    LINK_FIRST_VISIT = "LINK_FIRST_VISIT"
    WEBHOOK_DELIVERY_FAILED = "WEBHOOK_DELIVERY_FAILED"
    SECURITY_SCAN_WARNING = "SECURITY_SCAN_WARNING"
    TEST = "TEST"


class DevicePairingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONSUMED = "CONSUMED"
    EXPIRED = "EXPIRED"


class DeviceSessionStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"
    EXPIRED = "EXPIRED"
