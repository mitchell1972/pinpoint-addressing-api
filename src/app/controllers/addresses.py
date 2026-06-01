from fastapi import APIRouter, Depends

from app.core.db import get_conn
from app.core.errors import NotFoundError
from app.dependencies.auth import require_principal
from app.schemas.addresses import AddressCreate, AddressOut, ClaimRequest
from app.services import addresses as service

router = APIRouter()


@router.post("/addresses", response_model=AddressOut, status_code=201)
async def create_address(
    body: AddressCreate,
    principal=Depends(require_principal),
    conn=Depends(get_conn),
):
    """Create/claim a digital address for a GPS point (spec §6.1). Owned by the creator."""
    return AddressOut(**await service.create(conn, body, principal.account_id))


@router.post("/addresses/{code}/claim", response_model=AddressOut)
async def claim_address(
    code: str,
    body: ClaimRequest,
    principal=Depends(require_principal),
    conn=Depends(get_conn),
):
    """Claim (and optionally rename) a saved address — home/shop/warehouse (spec §6.1)."""
    return AddressOut(**await service.claim(conn, code, principal.account_id, body.alias))


@router.get("/addresses/{code}", response_model=AddressOut)
async def resolve_address(
    code: str,
    principal=Depends(require_principal),
    conn=Depends(get_conn),
):
    """Resolve a code to coordinates + metadata (spec §9.4)."""
    row = await service.get(conn, code)
    if row is None:
        raise NotFoundError("Address not found.")
    return AddressOut(**row)
