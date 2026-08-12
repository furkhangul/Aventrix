import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_client_ip, get_current_active_user
from app.core import audit_actions
from app.core.database import get_db
from app.models.enums import AuditResult, CampaignStatus
from app.models.user import User
from app.models.campaign import Campaign
from app.schemas.campaign import (
    CampaignCreateRequest,
    CampaignPublic,
    CampaignUpdateRequest,
    CampaignWithStats,
)
from app.schemas.common import PaginatedResponse
from app.services import campaign_service
from app.services.audit_service import write_audit_log
from app.services.exceptions import NotFoundError

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def _with_stats(campaign: Campaign, stats: dict) -> CampaignWithStats:
    return CampaignWithStats(
        id=campaign.id,
        name=campaign.name,
        description=campaign.description,
        status=campaign.status,
        tags=campaign.tags,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
        link_count=stats.get("link_count", 0),
        total_visits=stats.get("total_visits", 0),
        unique_visitors=stats.get("unique_visitors", 0),
    )


@router.post("", response_model=CampaignPublic, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    body: CampaignCreateRequest,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    campaign = await campaign_service.create_campaign(db, user_id=user.id, data=body)
    await write_audit_log(
        db,
        action=audit_actions.CAMPAIGN_CREATED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        resource_type="campaign",
        resource_id=str(campaign.id),
        ip_address=get_client_ip(request),
    )
    return campaign


@router.get("", response_model=PaginatedResponse[CampaignWithStats])
async def list_campaigns(
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    status_filter: CampaignStatus | None = None,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await campaign_service.list_campaigns(
        db, user_id=user.id, page=page, page_size=page_size, search=search, status=status_filter
    )
    stats_map = await campaign_service.get_campaign_stats_map(db, [c.id for c in items])
    return PaginatedResponse(
        items=[_with_stats(c, stats_map.get(c.id, {})) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{campaign_id}", response_model=CampaignWithStats)
async def get_campaign(
    campaign_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        campaign = await campaign_service.get_campaign_for_user(db, user_id=user.id, campaign_id=campaign_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    stats_map = await campaign_service.get_campaign_stats_map(db, [campaign.id])
    return _with_stats(campaign, stats_map.get(campaign.id, {}))


@router.patch("/{campaign_id}", response_model=CampaignPublic)
async def update_campaign(
    campaign_id: uuid.UUID,
    body: CampaignUpdateRequest,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        campaign = await campaign_service.update_campaign(
            db, user_id=user.id, campaign_id=campaign_id, data=body
        )
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    await write_audit_log(
        db,
        action=audit_actions.CAMPAIGN_UPDATED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        resource_type="campaign",
        resource_id=str(campaign_id),
        ip_address=get_client_ip(request),
    )
    return campaign


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await campaign_service.delete_campaign(db, user_id=user.id, campaign_id=campaign_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    await write_audit_log(
        db,
        action=audit_actions.CAMPAIGN_DELETED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        resource_type="campaign",
        resource_id=str(campaign_id),
        ip_address=get_client_ip(request),
    )
