import re

MIN_PASSWORD_LENGTH = 10


def validate_password_strength(password: str) -> str:
    """Raises ValueError with a user-facing message if the password is too weak."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain a lowercase letter")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain an uppercase letter")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain a digit")
    return password


def normalize_email(email: str) -> str:
    return email.strip().lower()
