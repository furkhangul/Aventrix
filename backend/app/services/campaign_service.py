import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign
from app.models.enums import CampaignStatus
from app.models.link import Link
from app.models.visit import Visit
from app.repositories.campaign_repository import get_owned_campaign
from app.schemas.campaign import CampaignCreateRequest, CampaignUpdateRequest
from app.services.exceptions import NotFoundError
from app.utils.pagination import paginate
from app.workers.queue import enqueue_webhook_event


async def create_campaign(db: AsyncSession, *, user_id: uuid.UUID, data: CampaignCreateRequest) -> Campaign:
    campaign = Campaign(
        user_id=user_id,
        name=data.name,
        description=data.description,
        tags=data.tags,
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    await enqueue_webhook_event(user_id, "campaign.created", {"campaign_id": str(campaign.id), "name": campaign.name})
    return campaign


async def list_campaigns(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    page: int,
    page_size: int,
    search: str | None = None,
    status: CampaignStatus | None = None,
) -> tuple[list[Campaign], int]:
    stmt = select(Campaign).where(Campaign.user_id == user_id)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(or_(Campaign.name.ilike(like), Campaign.description.ilike(like)))
    if status:
        stmt = stmt.where(Campaign.status == status)
    stmt = stmt.order_by(Campaign.created_at.desc())
    return await paginate(db, stmt, page=page, page_size=page_size)


async def get_campaign_for_user(db: AsyncSession, *, user_id: uuid.UUID, campaign_id: uuid.UUID) -> Campaign:
    campaign = await get_owned_campaign(db, user_id=user_id, campaign_id=campaign_id)
    if not campaign:
        raise NotFoundError()
    return campaign


async def update_campaign(
    db: AsyncSession, *, user_id: uuid.UUID, campaign_id: uuid.UUID, data: CampaignUpdateRequest
) -> Campaign:
    campaign = await get_campaign_for_user(db, user_id=user_id, campaign_id=campaign_id)
    previous_status = campaign.status
    if data.name is not None:
        campaign.name = data.name
    if data.description is not None:
        campaign.description = data.description
    if data.tags is not None:
        campaign.tags = data.tags
    if data.status is not None:
        campaign.status = data.status
    await db.commit()
    await db.refresh(campaign)

    if data.status == CampaignStatus.ARCHIVED and previous_status != CampaignStatus.ARCHIVED:
        await enqueue_webhook_event(
            user_id, "campaign.completed", {"campaign_id": str(campaign.id), "name": campaign.name}
        )
    return campaign


async def delete_campaign(db: AsyncSession, *, user_id: uuid.UUID, campaign_id: uuid.UUID) -> None:
    campaign = await get_campaign_for_user(db, user_id=user_id, campaign_id=campaign_id)
    await db.delete(campaign)
    await db.commit()


async def get_campaign_stats_map(db: AsyncSession, campaign_ids: list[uuid.UUID]) -> dict[uuid.UUID, dict]:
    """Batched (not N+1) link/visit counts for a set of campaigns, e.g. for a list view."""
    if not campaign_ids:
        return {}

    link_counts = dict(
        (
            await db.execute(
                select(Link.campaign_id, func.count())
                .where(Link.campaign_id.in_(campaign_ids))
                .group_by(Link.campaign_id)
            )
        ).all()
    )
    visit_counts = dict(
        (
            await db.execute(
                select(Visit.campaign_id, func.count())
                .where(Visit.campaign_id.in_(campaign_ids))
                .group_by(Visit.campaign_id)
            )
        ).all()
    )
    unique_counts = dict(
        (
            await db.execute(
                select(Visit.campaign_id, func.count(func.distinct(Visit.visitor_hash)))
                .where(Visit.campaign_id.in_(campaign_ids), Visit.visitor_hash.is_not(None))
                .group_by(Visit.campaign_id)
            )
        ).all()
    )

    return {
        cid: {
            "link_count": link_counts.get(cid, 0),
            "total_visits": visit_counts.get(cid, 0),
            "unique_visitors": unique_counts.get(cid, 0),
        }
        for cid in campaign_ids
    }
