"""Full API request audit log (spec §10).

Records every /v1 request (method, path, status, account if authenticated) to
request_log. Outermost middleware, so it captures the final status of everything,
including replays and auth failures. Logging must never break a request, and a
retention policy (repositories.audit.purge_request_logs) trims old rows.
"""

from starlette.middleware.base import BaseHTTPMiddleware

from app.core.db import open_pool
from app.repositories import audit as repo


class RequestAuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/v1/"):
            principal = getattr(request.state, "principal", None)
            account_id = principal.account_id if principal else None
            try:
                pool = await open_pool()
                async with pool.connection() as conn:
                    await repo.log_request(
                        conn, account_id, request.method, request.url.path, response.status_code
                    )
            except Exception:
                pass
        return response
