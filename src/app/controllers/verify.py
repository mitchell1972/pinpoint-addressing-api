from fastapi import APIRouter, Depends

from app.core.db import get_conn
from app.dependencies.auth import require_principal
from app.schemas.verify import VerifyRequest, VerifyResponse
from app.services import verify as service

router = APIRouter()


@router.post("/verify", response_model=VerifyResponse)
async def verify_address(
    body: VerifyRequest,
    principal=Depends(require_principal),
    conn=Depends(get_conn),
):
    """Confirm an address resolves to a real mapped location (spec §6.3)."""
    return VerifyResponse(**await service.verify(conn, body))
