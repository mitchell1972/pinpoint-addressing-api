from fastapi import Depends, Request, Response

from app.core import rate_limit
from app.core.db import get_conn
from app.core.errors import ForbiddenError
from app.core.security import Principal
from app.services import auth as auth_service


async def require_principal(
    request: Request,
    response: Response,
    conn=Depends(get_conn),
) -> Principal:
    """Controller-side auth dependency.

    Resolves the API key to a principal, enforces the per-key rate limit, and
    sets the X-RateLimit-* headers on the response. Stores the principal on
    request.state so the metering middleware can attribute the call afterwards.
    """
    principal = await auth_service.resolve_principal(conn, request.headers.get("Authorization", ""))
    request.state.principal = principal

    # Enforce the limit; raises 429 (with Retry-After) when exceeded.
    remaining = rate_limit.check(principal.api_key_id, principal.rate_limit)
    response.headers["X-RateLimit-Limit"] = str(principal.rate_limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return principal


async def require_admin(principal: Principal = Depends(require_principal)) -> Principal:
    """Gate admin-only endpoints (account/key management)."""
    if principal.scope != "admin":
        raise ForbiddenError("Admin scope required.")
    return principal
