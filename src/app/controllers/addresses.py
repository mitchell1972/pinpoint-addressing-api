from fastapi import APIRouter, Depends

from app.core.db import get_conn
from app.core.errors import NotFoundError
from app.dependencies.auth import require_principal
from app.schemas.addresses import AddressCreate, AddressOut
from app.services import addresses as service

router = APIRouter()


@router.post("/addresses", response_model=AddressOut, status_code=201)
async def create_address(
    body: AddressCreate,
    principal=Depends(require_principal),
    conn=Depends(get_conn),
):
    """Create/claim a digital address for a GPS point (spec §6.1)."""
    return AddressOut(**await service.create(conn, body))


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
