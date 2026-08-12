from fastapi import APIRouter

from app.api.v1.analytics import router as analytics_router
from app.api.v1.api_keys import router as api_keys_router
from app.api.v1.auth import router as auth_router
from app.api.v1.campaigns import router as campaigns_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.devices import router as devices_router
from app.api.v1.links import router as links_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.qr import router as qr_router
from app.api.v1.security_center import router as security_center_router
from app.api.v1.tracking import router as tracking_router
from app.api.v1.url_tools import router as url_tools_router
from app.api.v1.webhooks import router as webhooks_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(campaigns_router)
api_router.include_router(links_router)
api_router.include_router(dashboard_router)
api_router.include_router(tracking_router)
api_router.include_router(analytics_router)
api_router.include_router(qr_router)
api_router.include_router(url_tools_router)
api_router.include_router(security_center_router)
api_router.include_router(api_keys_router)
api_router.include_router(webhooks_router)
api_router.include_router(notifications_router)
api_router.include_router(devices_router)
