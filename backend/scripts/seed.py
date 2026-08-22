"""
Development seed: ensures a super-admin account exists so there's a way
into a freshly-created database. Never writes a hardcoded credential — the
password is randomly generated and printed exactly once. Idempotent: if the
account already exists, its password is left untouched. Run via
`python -m scripts.seed` (already wired into docker-compose's backend
startup command).
"""

import asyncio
import logging
import secrets

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import get_user_by_email

logger = logging.getLogger("aventrix.seed")
settings = get_settings()


async def seed_admin() -> None:
    if settings.is_production:
        logger.info(
            "Skipping auto-created admin account in production. "
            "Create the first admin manually (register, then promote the role in the database)."
        )
        return

    async with AsyncSessionLocal() as db:
        existing = await get_user_by_email(db, settings.seed_admin_email)
        if existing:
            print(f"[seed] Admin account already exists: {settings.seed_admin_email}")
            return

        password = secrets.token_urlsafe(18)
        admin = User(
            email=settings.seed_admin_email,
            hashed_password=hash_password(password),
            full_name="Super Admin",
            role=UserRole.SUPER_ADMIN,
            is_active=True,
            is_email_verified=True,
        )
        db.add(admin)
        await db.commit()

        print("=" * 72)
        print("[seed] Created development admin account:")
        print(f"[seed]   email:    {settings.seed_admin_email}")
        print(f"[seed]   password: {password}")
        print("[seed] This password is shown once and is not stored anywhere in plaintext.")
        print("=" * 72)


if __name__ == "__main__":
    asyncio.run(seed_admin())
