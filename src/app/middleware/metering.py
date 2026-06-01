"""Usage metering.

Runs after each request and records one usage_event for billable endpoints on a
successful, authenticated response. (Rate-limit headers are set, and the limit
enforced, by the auth dependency — see core/rate_limit.py.)

Metering must never break a request, so DB failures here are swallowed (a real
deployment would emit to a dead-letter/metric instead of `pass`).
"""

from starlette.middleware.base import BaseHTTPMiddleware

from app.core.db import open_pool
from app.services import metering as metering_service

# Endpoints that consume billable units (spec §8). Resolve-by-code metering and
# per-query batch billing are deliberate TODOs.
_BILLABLE = {"/v1/geocode", "/v1/reverse", "/v1/batch/geocode", "/v1/verify"}


class MeteringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        principal = getattr(request.state, "principal", None)
        if principal is None:
            return response

        if request.url.path in _BILLABLE and response.status_code < 400:
            try:
                pool = await open_pool()
                async with pool.connection() as conn:
                    await metering_service.record(conn, principal.account_id, request.url.path)
            except Exception:
                pass

        return response
