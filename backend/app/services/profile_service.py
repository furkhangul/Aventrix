import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.user import User
from app.services.exceptions import ServiceError

settings = get_settings()

UPLOAD_ROOT = Path(__file__).resolve().parent.parent.parent / "uploads"
AVATAR_DIR = UPLOAD_ROOT / "avatars"
ALLOWED_AVATAR_TYPES = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
MAX_AVATAR_BYTES = 2 * 1024 * 1024  # 2MB


class UnsupportedAvatarTypeError(ServiceError):
    pass


class AvatarTooLargeError(ServiceError):
    pass


async def update_profile(db: AsyncSession, user: User, *, full_name: str | None) -> User:
    if full_name is not None:
        user.full_name = full_name
    await db.commit()
    return user


async def update_avatar(db: AsyncSession, user: User, file: UploadFile) -> User:
    content_type = file.content_type or ""
    if content_type not in ALLOWED_AVATAR_TYPES:
        raise UnsupportedAvatarTypeError("Only PNG, JPEG, or WEBP images are allowed")

    contents = await file.read()
    if len(contents) > MAX_AVATAR_BYTES:
        raise AvatarTooLargeError("Avatar must be 2MB or smaller")

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    extension = ALLOWED_AVATAR_TYPES[content_type]
    # Filename is never derived from user input — avoids path traversal entirely.
    filename = f"{uuid.uuid4().hex}{extension}"
    destination = AVATAR_DIR / filename
    destination.write_bytes(contents)

    user.avatar_url = f"/uploads/avatars/{filename}"
    await db.commit()
    return user
