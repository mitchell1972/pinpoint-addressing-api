from fastapi import APIRouter, Depends

from app.core.db import get_conn
from app.dependencies.auth import require_admin
from app.schemas.accounts import AccountCreate, AccountOut, KeyCreate, KeyIssued
from app.services import accounts as service

router = APIRouter()


@router.post("/accounts", response_model=AccountOut, status_code=201)
async def create_account(
    body: AccountCreate,
    principal=Depends(require_admin),
    conn=Depends(get_conn),
):
    row = await service.create_account(conn, body.name, body.type, body.tier)
    return AccountOut(
        id=str(row["id"]),
        name=row["name"],
        type=row["type"],
        tier=row["tier"],
        status=row["status"],
    )


@router.post("/accounts/{account_id}/keys", response_model=KeyIssued, status_code=201)
async def issue_key(
    account_id: str,
    body: KeyCreate,
    principal=Depends(require_admin),
    conn=Depends(get_conn),
):
    return KeyIssued(
        **await service.issue_key(conn, account_id, body.env, body.scope, body.rate_limit)
    )


@router.post("/keys/{key_id}/revoke", status_code=204)
async def revoke_key(
    key_id: str,
    principal=Depends(require_admin),
    conn=Depends(get_conn),
):
    await service.revoke_key(conn, key_id)
