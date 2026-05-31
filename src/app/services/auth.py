from app.core.errors import UnauthorizedError
from app.core.security import Principal, hash_key
from app.repositories import auth as repo

_BEARER = "Bearer "


def _unauthorized() -> UnauthorizedError:
    return UnauthorizedError("Missing or invalid API key.", headers={"WWW-Authenticate": "Bearer"})


async def resolve_principal(conn, authorization: str) -> Principal:
    """Resolve `Authorization: Bearer pk_(test|live)_...` to a Principal."""
    if not authorization.startswith(_BEARER):
        raise _unauthorized()

    raw = authorization[len(_BEARER):].strip()
    if raw.startswith("pk_test_"):
        claimed_env = "test"
    elif raw.startswith("pk_live_"):
        claimed_env = "live"
    else:
        raise _unauthorized()

    row = await repo.find_active_key(conn, hash_key(raw))
    # Unknown key, or a key whose prefix lies about its environment.
    if row is None or row["env"] != claimed_env:
        raise _unauthorized()

    return Principal(
        account_id=str(row["account_id"]),
        account_type=row["account_type"],
        api_key_id=str(row["api_key_id"]),
        env=row["env"],
        rate_limit=row["rate_limit"],
    )
