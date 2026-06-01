from psycopg import errors

from app.core.errors import AppError, ForbiddenError, NotFoundError
from app.lib.codes import new_alias
from app.lib.geohash import encode as geohash_encode
from app.lib.olc import encode as olc_encode
from app.repositories import addresses as repo
from app.schemas.addresses import AddressCreate


async def create(conn, data: AddressCreate, owner_account_id: str | None = None) -> dict:
    """Create/claim a digital address: derive Plus Code + geohash, allocate a
    unique human alias (retry on the rare collision), persist. The creating
    account becomes the owner."""
    olc = olc_encode(data.lat, data.lng)
    geohash = geohash_encode(data.lat, data.lng)

    for _ in range(5):
        try:
            return await repo.create_address(
                conn, data, new_alias(), olc, geohash, owner_account_id
            )
        except errors.UniqueViolation:
            continue
    raise AppError("Could not allocate a unique address code.")


async def get(conn, code: str) -> dict | None:
    return await repo.get_by_code(conn, code)


async def claim(conn, code: str, account_id: str, alias: str | None) -> dict:
    """Claim and optionally rename an address; fails if another account owns it."""
    addr = await repo.get_by_code(conn, code)
    if addr is None:
        raise NotFoundError("Address not found.")
    owner = addr["owner_account_id"]
    if owner is not None and str(owner) != account_id:
        raise ForbiddenError("Address is already claimed by another account.")
    await repo.claim(conn, code, account_id, alias)
    return await repo.get_by_code(conn, code)
