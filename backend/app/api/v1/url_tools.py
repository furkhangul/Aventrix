from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_active_user
from app.core.config import get_settings
from app.core.rate_limit import rate_limit
from app.models.user import User
from app.schemas.url_tools import (
    RedirectCheckRequest,
    RedirectCheckResponse,
    UrlAnalyzeRequest,
    UrlAnalyzeResponse,
)
from app.services import url_tools_service
from app.services.exceptions import InvalidUrlError

router = APIRouter(prefix="/url-tools", tags=["url-tools"])
settings = get_settings()


@router.post(
    "/analyze",
    response_model=UrlAnalyzeResponse,
    dependencies=[Depends(rate_limit(20, window_seconds=60, scope="url-tools-analyze"))],
)
async def analyze(body: UrlAnalyzeRequest, user: User = Depends(get_current_active_user)):
    try:
        return await url_tools_service.analyze_url(body.url)
    except InvalidUrlError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post(
    "/redirect-check",
    response_model=RedirectCheckResponse,
    dependencies=[Depends(rate_limit(20, window_seconds=60, scope="url-tools-redirect"))],
)
async def redirect_check(body: RedirectCheckRequest, user: User = Depends(get_current_active_user)):
    try:
        return await url_tools_service.check_redirects(body.url)
    except InvalidUrlError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
