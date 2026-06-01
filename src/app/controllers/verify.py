from fastapi import APIRouter, Depends, Request

from app.core.db import get_conn
from app.dependencies.auth import require_principal
from app.schemas.verify import VerifyRequest, VerifyResponse
from app.services import verify as service

router = APIRouter()


@router.post("/verify", response_model=VerifyResponse)
async def verify_address(
    body: VerifyRequest,
    request: Request,
    principal=Depends(require_principal),
    conn=Depends(get_conn),
):
    """Confirm an address resolves to a real mapped location (spec §6.3).

    KYC mode also writes a tamper-evident audit entry with the captured evidence.
    """
    evidence = {
        "device": body.device,
        "agent": body.agent,
        "ip": request.client.host if request.client else None,
    }
    return VerifyResponse(**await service.verify(conn, body, evidence=evidence))
