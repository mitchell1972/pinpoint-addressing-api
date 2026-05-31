from fastapi import Depends, Request

from app.core.db import get_conn
from app.core.security import Principal
from app.services import auth as auth_service


async def require_principal(request: Request, conn=Depends(get_conn)) -> Principal:
    """Controller-side auth dependency.

    Delegates to the auth service, then stores the principal on request.state so
    the metering middleware can attribute the call after the response is produced.
    """
    principal = await auth_service.resolve_principal(conn, request.headers.get("Authorization", ""))
    request.state.principal = principal
    return principal
