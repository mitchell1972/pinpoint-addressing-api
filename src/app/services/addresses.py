from psycopg import errors

from app.core.errors import AppError
from app.lib.codes import new_alias
from app.lib.geohash import encode as geohash_encode
from app.lib.olc import encode as olc_encode
from app.repositories import addresses as repo
from app.schemas.addresses import AddressCreate


async def create(conn, data: AddressCreate) -> dict:
    """Create/claim a digital address: derive Plus Code + geohash, allocate a
    unique human alias (retry on the rare collision), persist."""
    olc = olc_encode(data.lat, data.lng)
    geohash = geohash_encode(data.lat, data.lng)

    for _ in range(5):
        try:
            return await repo.create_address(conn, data, new_alias(), olc, geohash)
        except errors.UniqueViolation:
            continue
    raise AppError("Could not allocate a unique address code.")


async def get(conn, code: str) -> dict | None:
    return await repo.get_by_code(conn, code)
