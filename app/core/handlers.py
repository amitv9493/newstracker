import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, DisconnectionError, IntegrityError

from app.core.exceptions import AppError, ConflictError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            "%s %s failed: %s",
            request.method,
            request.url.path,
            exc.detail,
        )
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(ConflictError)
    async def conflict_error_handler(
        request: Request, exc: ConflictError
    ) -> JSONResponse:
        logger.warning(
            "conflict on %s %s: %s",
            request.method,
            request.url.path,
            exc.detail,
        )
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(
        request: Request, exc: IntegrityError
    ) -> JSONResponse:
        logger.warning(
            "integrity error on %s %s",
            request.method,
            request.url.path,
            exc_info=exc,
        )
        return JSONResponse(
            status_code=409,
            content={"detail": "resource already exists"},
        )

    @app.exception_handler(DBAPIError)
    @app.exception_handler(DisconnectionError)
    async def database_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(
            "database error on %s %s",
            request.method,
            request.url.path,
        )
        return JSONResponse(
            status_code=503,
            content={"detail": "database unavailable"},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled error on %s %s",
            request.method,
            request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "internal server error"},
        )
