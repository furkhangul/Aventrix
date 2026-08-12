import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_feature
from app.core.database import get_db
from app.models.user import User
from app.repositories.link_repository import get_owned_link
from app.services import qr_service
from app.services.exceptions import ServiceError
from app.services.link_url import build_short_url

router = APIRouter(prefix="/qr", tags=["qr"], dependencies=[Depends(require_feature("enable_qr"))])


def _render_qr(
    data: str,
    *,
    size: int,
    fg_color: str,
    bg_color: str,
    error_correction: str,
    format: str,
    logo_id: str | None,
) -> Response:
    try:
        if format == "svg":
            content = qr_service.generate_qr_svg(data, error_correction=error_correction)
            media_type = "image/svg+xml"
        elif format == "png":
            logo_path = qr_service.logo_path_for(logo_id) if logo_id else None
            content = qr_service.generate_qr_png(
                data,
                size=size,
                fg_color=fg_color,
                bg_color=bg_color,
                error_correction=error_correction,
                logo_path=logo_path,
            )
            media_type = "image/png"
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="format must be 'png' or 'svg'")
    except ServiceError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return Response(content=content, media_type=media_type)


@router.get("/generate")
async def generate_qr(
    data: str = Query(min_length=1, max_length=2048),
    size: int = 300,
    fg_color: str = "000000",
    bg_color: str = "FFFFFF",
    error_correction: str = "M",
    format: str = "png",
    logo_id: str | None = None,
    user: User = Depends(get_current_active_user),
):
    return _render_qr(
        data, size=size, fg_color=fg_color, bg_color=bg_color, error_correction=error_correction, format=format, logo_id=logo_id
    )


@router.get("/links/{link_id}")
async def generate_qr_for_link(
    link_id: uuid.UUID,
    size: int = 300,
    fg_color: str = "000000",
    bg_color: str = "FFFFFF",
    error_correction: str = "M",
    format: str = "png",
    logo_id: str | None = None,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    link = await get_owned_link(db, user_id=user.id, link_id=link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    return _render_qr(
        build_short_url(link.short_code),
        size=size,
        fg_color=fg_color,
        bg_color=bg_color,
        error_correction=error_correction,
        format=format,
        logo_id=logo_id,
    )


@router.post("/logo")
async def upload_logo(file: UploadFile, user: User = Depends(get_current_active_user)):
    try:
        logo_id = await qr_service.upload_logo(file)
    except ServiceError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return {"logo_id": logo_id, "url": f"/uploads/qr-logos/{logo_id}"}
