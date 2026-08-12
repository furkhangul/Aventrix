import logging

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("furoftheweak.errors")


def _envelope(message: str, code: int, details: object | None = None) -> dict:
    body: dict = {"error": {"message": message, "code": code}}
    if details is not None:
        body["error"]["details"] = details
    return body


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(str(exc.detail), exc.status_code),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # exc.errors() can embed the raw exception object in ctx.error for
        # validators that re-raise ValueError — jsonable_encoder is what
        # FastAPI's own default handler uses to make that JSON-safe.
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_envelope(
                "Invalid request data",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                details=jsonable_encoder(exc.errors()),
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Never leak internals (stack traces, secrets) to the client.
        logger.exception("unhandled_exception", extra={"path": str(request.url.path)})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_envelope("Internal server error", status.HTTP_500_INTERNAL_SERVER_ERROR),
        )
