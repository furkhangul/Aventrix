from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.redirect import router as redirect_router
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.services.profile_service import UPLOAD_ROOT
from app.workers.queue import get_redis_client

configure_logging()
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    # Swagger UI and the raw OpenAPI schema are handy in dev but not
    # something to leave open on a live instance by default.
    docs_url=None if settings.is_production else "/api/docs",
    openapi_url=None if settings.is_production else "/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)

register_exception_handlers(app)
app.include_router(api_router)
app.include_router(redirect_router)

UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_ROOT), check_dir=False), name="uploads")


@app.get("/health", tags=["system"])
async def health() -> dict:
    """Liveness probe: the process is up. Does not check dependencies — use /ready for that."""
    return {"status": "ok"}


@app.get("/ready", tags=["system"])
async def ready() -> JSONResponse:
    """Readiness probe: verifies the database and Redis are actually reachable."""
    components = {"database": "unknown", "redis": "unknown"}

    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        components["database"] = "ok"
    except Exception:
        components["database"] = "unavailable"

    try:
        await get_redis_client().ping()
        components["redis"] = "ok"
    except Exception:
        components["redis"] = "unavailable"

    all_ok = all(v == "ok" for v in components.values())
    return JSONResponse(
        status_code=status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "ok" if all_ok else "degraded", "components": components},
    )
