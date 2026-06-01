from fastapi import APIRouter, Depends

from app.core.db import get_conn
from app.dependencies.auth import require_principal
from app.schemas.sync import SyncRequest, SyncResult
from app.services import sync as service

router = APIRouter()


@router.post("/sync", response_model=SyncResult, status_code=201)
async def sync_captures(
    body: SyncRequest,
    principal=Depends(require_principal),
    conn=Depends(get_conn),
):
    """Upload a queue of offline captures (spec §9.7). Idempotent per capture_id."""
    captures = [c.model_dump() for c in body.captures]
    return SyncResult(**await service.sync(conn, captures, principal.account_id))
