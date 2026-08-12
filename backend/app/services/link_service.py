import uuid
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from app.core.security import hash_password
from app.models.enums import CampaignStatus
from app.models.link import Link
from app.models.visit import Visit
from app.repositories.campaign_repository import get_owned_campaign
from app.repositories.link_repository import get_owned_link, short_code_exists
from app.schemas.link import LinkCreateRequest, LinkUpdateRequest
from app.services import notification_service
from app.services.exceptions import ConflictError, NotFoundError
from app.utils.pagination import MAX_PAGE_SIZE, paginate
from app.utils.short_code import generate_short_code
from app.workers.queue import enqueue_webhook_event

MAX_SHORT_CODE_ATTEMPTS = 10


async def generate_unique_short_code(db: AsyncSession) -> str:
    for _ in range(MAX_SHORT_CODE_ATTEMPTS):
        code = generate_short_code()
        if not await short_code_exists(db, code):
            return code
    raise RuntimeError("Could not generate a unique short code — this should not happen")


async def create_link(db: AsyncSession, *, user_id: uuid.UUID, data: LinkCreateRequest) -> Link:
    campaign = None
    if data.campaign_id is not None:
        campaign = await get_owned_campaign(db, user_id=user_id, campaign_id=data.campaign_id)
        if not campaign:
            raise NotFoundError("Campaign not found")
        if campaign.status == CampaignStatus.ARCHIVED:
            raise ConflictError("Cannot add a link to an archived campaign")

    if data.custom_alias:
        if await short_code_exists(db, data.custom_alias):
            raise ConflictError("This alias is already taken")
        short_code = data.custom_alias
    else:
        short_code = await generate_unique_short_code(db)

    link = Link(
        user_id=user_id,
        campaign_id=data.campaign_id,
        short_code=short_code,
        target_url=data.target_url,
        description=data.description,
        tags=data.tags,
        expires_at=data.expires_at,
        is_password_protected=bool(data.password),
        password_hash=hash_password(data.password) if data.password else None,
        requires_consent=data.requires_consent,
        utm_params=data.utm.to_dict(),
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    link.campaign = campaign  # already loaded above; avoids a second query for _to_public()

    await enqueue_webhook_event(
        user_id,
        "link.created",
        {"link_id": str(link.id), "short_code": link.short_code, "target_url": link.target_url},
    )
    return link


async def list_links(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    page: int,
    page_size: int,
    search: str | None = None,
    campaign_id: uuid.UUID | None = None,
    is_active: bool | None = None,
) -> tuple[list[Link], int]:
    stmt = select(Link).where(Link.user_id == user_id).options(selectinload(Link.campaign))
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            or_(Link.short_code.ilike(like), Link.description.ilike(like), Link.target_url.ilike(like))
        )
    if campaign_id is not None:
        stmt = stmt.where(Link.campaign_id == campaign_id)
    if is_active is not None:
        stmt = stmt.where(Link.is_active == is_active)
    stmt = stmt.order_by(Link.created_at.desc())
    return await paginate(db, stmt, page=page, page_size=page_size)


async def get_link_for_user(db: AsyncSession, *, user_id: uuid.UUID, link_id: uuid.UUID) -> Link:
    link = await get_owned_link(db, user_id=user_id, link_id=link_id)
    if not link:
        raise NotFoundError()
    return link


async def update_link(db: AsyncSession, *, user_id: uuid.UUID, link_id: uuid.UUID, data: LinkUpdateRequest) -> Link:
    link = await get_link_for_user(db, user_id=user_id, link_id=link_id)

    if data.campaign_id is not None:
        campaign = await get_owned_campaign(db, user_id=user_id, campaign_id=data.campaign_id)
        if not campaign:
            raise NotFoundError("Campaign not found")
        if campaign.status == CampaignStatus.ARCHIVED:
            raise ConflictError("Cannot move a link into an archived campaign")
        link.campaign_id = data.campaign_id
        link.campaign = campaign  # keep the in-memory relationship in sync with the FK above
    if data.target_url is not None:
        link.target_url = data.target_url
    if data.description is not None:
        link.description = data.description
    if data.tags is not None:
        link.tags = data.tags
    if data.expires_at is not None:
        link.expires_at = data.expires_at
    if data.is_active is not None:
        link.is_active = data.is_active
    if data.requires_consent is not None:
        link.requires_consent = data.requires_consent

    await db.commit()
    await db.refresh(link)
    return link


async def set_link_password(db: AsyncSession, *, user_id: uuid.UUID, link_id: uuid.UUID, password: str | None) -> Link:
    link = await get_link_for_user(db, user_id=user_id, link_id=link_id)
    if password:
        link.is_password_protected = True
        link.password_hash = hash_password(password)
    else:
        link.is_password_protected = False
        link.password_hash = None
    await db.commit()
    await db.refresh(link)
    return link


async def delete_link(db: AsyncSession, *, user_id: uuid.UUID, link_id: uuid.UUID) -> None:
    link = await get_link_for_user(db, user_id=user_id, link_id=link_id)
    await db.delete(link)
    await db.commit()


async def get_link_stats_map(db: AsyncSession, link_ids: list[uuid.UUID]) -> dict[uuid.UUID, dict]:
    """Batched (not N+1) visit counts for a set of links, e.g. for a list view."""
    if not link_ids:
        return {}

    visit_counts = dict(
        (
            await db.execute(
                select(Visit.link_id, func.count()).where(Visit.link_id.in_(link_ids)).group_by(Visit.link_id)
            )
        ).all()
    )
    unique_counts = dict(
        (
            await db.execute(
                select(Visit.link_id, func.count(func.distinct(Visit.visitor_hash)))
                .where(Visit.link_id.in_(link_ids), Visit.visitor_hash.is_not(None))
                .group_by(Visit.link_id)
            )
        ).all()
    )
    return {
        lid: {
            "total_visits": visit_counts.get(lid, 0),
            "unique_visitors": unique_counts.get(lid, 0),
        }
        for lid in link_ids
    }


async def list_link_visits(
    db: AsyncSession, *, link_id: uuid.UUID, page: int, page_size: int
) -> tuple[list[tuple[Visit, int | None]], int]:
    """
    Per-visitor breakdown for a single link, most recent first. Each visit
    is paired with its 1-based sequence number among visits sharing the same
    visitor_hash on this link (1 = that visitor's first click here), so the
    API can flag returning visitors — None when there's no visitor_hash
    (i.e. consent was withheld, so visits can't be attributed to a visitor).
    """
    page = max(page, 1)
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)

    total = (
        await db.execute(select(func.count()).select_from(Visit).where(Visit.link_id == link_id))
    ).scalar_one()

    other = aliased(Visit)
    visit_number = (
        select(func.count())
        .select_from(other)
        .where(
            other.link_id == Visit.link_id,
            other.visitor_hash == Visit.visitor_hash,
            other.created_at <= Visit.created_at,
        )
        .correlate(Visit)
        .scalar_subquery()
    )

    stmt = (
        select(Visit, visit_number)
        .where(Visit.link_id == link_id)
        .order_by(Visit.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(stmt)).all()
    items = [(visit, number if visit.visitor_hash else None) for visit, number in rows]
    return items, total


async def sweep_expired_links(db: AsyncSession) -> int:
    """
    Periodic worker task: notifies the owner of each link that has just
    expired, exactly once (guarded by expiry_notified_at). Returns the
    number of links notified.
    """
    now = datetime.now(timezone.utc)
    stmt = select(Link).where(
        Link.is_active.is_(True),
        Link.expires_at.is_not(None),
        Link.expires_at <= now,
        Link.expiry_notified_at.is_(None),
    )
    links = (await db.execute(stmt)).scalars().all()
    for link in links:
        link.expiry_notified_at = now
        await notification_service.notify_link_expired(
            db, user_id=link.user_id, short_code=link.short_code, link_id=link.id
        )
    if links:
        await db.commit()
    return len(links)
