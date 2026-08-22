import re
import secrets
import string

ALPHABET = string.ascii_letters + string.digits
DEFAULT_LENGTH = 7

ALIAS_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,64}$")

# Reserved words that must never be usable as a custom alias — they'd collide
# with real routes or be used for phishing lookalikes of the app itself.
RESERVED_WORDS = {
    "api",
    "app",
    "admin",
    "administrator",
    "auth",
    "login",
    "logout",
    "register",
    "signup",
    "signin",
    "dashboard",
    "settings",
    "account",
    "campaigns",
    "campaign",
    "links",
    "link",
    "analytics",
    "security",
    "reports",
    "report",
    "webhooks",
    "webhook",
    "notifications",
    "docs",
    "static",
    "assets",
    "uploads",
    "health",
    "ready",
    "t",
    "r",
    "www",
    "mail",
    "ftp",
    "root",
    "null",
    "undefined",
    "aventrix",
    "support",
    "help",
    "about",
    "terms",
    "privacy",
    "verify-email",
    "reset-password",
    "forgot-password",
    "consent",
    "not-found",
    "gate",
}


def generate_short_code(length: int = DEFAULT_LENGTH) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def is_valid_alias_format(alias: str) -> bool:
    return bool(ALIAS_PATTERN.match(alias))


def is_reserved(alias: str) -> bool:
    return alias.lower() in RESERVED_WORDS
