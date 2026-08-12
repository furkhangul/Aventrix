import secrets

import pyotp

from app.core.config import get_settings

settings = get_settings()

BACKUP_CODE_COUNT = 10


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def get_provisioning_uri(secret: str, email: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=settings.app_name)


def verify_totp_code(secret: str, code: str) -> bool:
    try:
        return pyotp.TOTP(secret).verify(code, valid_window=1)
    except Exception:
        return False


def generate_backup_codes(count: int = BACKUP_CODE_COUNT) -> list[str]:
    return ["-".join([secrets.token_hex(2), secrets.token_hex(2)]) for _ in range(count)]
