from app.schemas.addresses import AddressCreate

_SELECT_BY_CODE = """
SELECT a.id, a.code, a.olc, a.alias, a.lat, a.lng, a.geohash,
       a.state, a.lga, a.ward, a.confidence, a.status, a.created_at,
       a.last_verified_at, a.verification_count,
       m.landmark, m.building_desc, m.access_notes, m.contact
FROM address a
LEFT JOIN address_metadata m ON m.address_id = a.id
WHERE a.code = %s
"""


async def get_by_code(conn, code: str) -> dict | None:
    async with conn.cursor() as cur:
        await cur.execute(_SELECT_BY_CODE, (code,))
        return await cur.fetchone()


async def create_address(conn, data: AddressCreate, code: str, olc: str, geohash: str) -> dict:
    """Insert the canonical row + metadata atomically, then return the joined view."""
    async with conn.transaction():
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO address (code, olc, alias, lat, lng, geohash, state, lga, ward, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'unverified')
                RETURNING id
                """,
                (
                    code,
                    olc,
                    data.alias,
                    data.lat,
                    data.lng,
                    geohash,
                    data.state,
                    data.lga,
                    data.ward,
                ),
            )
            address_id = (await cur.fetchone())["id"]

            if any([data.landmark, data.building_desc, data.access_notes, data.contact]):
                await cur.execute(
                    """
                    INSERT INTO address_metadata
                        (address_id, landmark, building_desc, access_notes, contact)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        address_id,
                        data.landmark,
                        data.building_desc,
                        data.access_notes,
                        data.contact,
                    ),
                )

    return await get_by_code(conn, code)


async def touch_verification(conn, code: str, confidence: float, verified_at) -> None:
    """Record a successful (re)verification: bump the count, refresh the
    timestamp, update running confidence, and mark the address verified."""
    await conn.execute(
        "UPDATE address SET last_verified_at = %s, verification_count = verification_count + 1, "
        "confidence = %s, status = 'verified' WHERE code = %s",
        (verified_at, confidence, code),
    )
