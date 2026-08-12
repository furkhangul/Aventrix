class ServiceError(Exception):
    """Base class for domain-level errors raised by the service layer."""


class EmailAlreadyRegisteredError(ServiceError):
    pass


class InvalidCredentialsError(ServiceError):
    pass


class AccountInactiveError(ServiceError):
    pass


class InvalidOrExpiredTokenError(ServiceError):
    pass


class TwoFactorRequiredError(ServiceError):
    def __init__(self, pending_token: str):
        self.pending_token = pending_token
        super().__init__("Two-factor authentication required")


class InvalidTwoFactorCodeError(ServiceError):
    pass


class TwoFactorAlreadyEnabledError(ServiceError):
    pass


class TwoFactorNotEnabledError(ServiceError):
    pass


class NotFoundError(ServiceError):
    pass


class PermissionDeniedError(ServiceError):
    pass


class ConflictError(ServiceError):
    pass


class InvalidUrlError(ServiceError):
    """Raised when a user-supplied URL fails deeper (DNS-resolution-based) SSRF validation."""

    pass
