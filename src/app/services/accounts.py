"""Account + API-key administration (admin-only).

Keys are generated here, hashed before storage, and the plaintext is returned
exactly once (the caller must save it — we can never show it again).
"""

import secrets
import uuid

from app.core.errors import NotFoundError
from app.repositories import accounts as repo


def _generate_key(env: str) -> str:
    return f"pk_{env}_{secrets.token_hex(16)}"


def _as_uuid(value: str, not_found: str):
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise NotFoundError(not_found) from exc


async def create_account(conn, name: str, type_: str, tier: str) -> dict:
    return await repo.create_account(conn, name, type_, tier)


async def issue_key(conn, account_id: str, env: str, scope: str, rate_limit: int) -> dict:
    acc = _as_uuid(account_id, "Account not found.")
    if not await repo.account_exists(conn, acc):
        raise NotFoundError("Account not found.")
    raw = _generate_key(env)
    row = await repo.create_api_key(conn, acc, raw, env, scope, rate_limit)
    return {
        "id": str(row["id"]),
        "key": raw,  # shown once
        "key_prefix": row["key_prefix"],
        "env": row["env"],
        "scope": row["scope"],
        "rate_limit": row["rate_limit"],
    }


async def revoke_key(conn, key_id: str) -> None:
    kid = _as_uuid(key_id, "Active key not found.")
    if not await repo.revoke_key(conn, kid):
        raise NotFoundError("Active key not found.")
