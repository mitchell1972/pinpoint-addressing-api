"""Domain exceptions + their HTTP mapping.

Controllers and services raise these; a single handler converts them to JSON.
This keeps controllers thin (no scattered HTTPException) and lets the service
layer stay framework-agnostic apart from importing these types.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code = 500

    def __init__(self, detail: str, headers: dict | None = None):
        self.detail = detail
        self.headers = headers
        super().__init__(detail)


class NotFoundError(AppError):
    status_code = 404


class UnauthorizedError(AppError):
    status_code = 401


class RateLimitedError(AppError):
    status_code = 429


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle_app_error(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )
