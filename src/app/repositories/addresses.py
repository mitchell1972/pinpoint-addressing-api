from app.schemas.addresses import AddressCreate

_SELECT_BY_CODE = """
SELECT a.id, a.code, a.olc, a.alias, a.lat, a.lng, a.geohash,
       a.state, a.lga, a.ward, a.confidence, a.status, a.consent, a.created_at,
       a.last_verified_at, a.verification_count, a.owner_account_id,
       m.landmark, m.building_desc, m.access_notes, m.contact
FROM address a
LEFT JOIN address_metadata m ON m.address_id = a.id
WHERE a.code = %s
"""


async def get_by_code(conn, code: str) -> dict | None:
    async with conn.cursor() as cur:
        await cur.execute(_SELECT_BY_CODE, (code,))
        return await cur.fetchone()


async def create_address(
    conn,
    data: AddressCreate,
    code: str,
    olc: str,
    geohash: str,
    owner_account_id: str | None = None,
) -> dict:
    """Insert the canonical row + metadata atomically, then return the joined view."""
    async with conn.transaction():
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO address
                    (code, olc, alias, lat, lng, geohash, state, lga, ward, status, consent, owner_account_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'unverified', %s, %s::uuid)
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
                    data.consent,
                    owner_account_id,
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


async def claim(conn, code: str, account_id: str, alias: str | None) -> dict | None:
    """Take ownership (and optionally rename) an address that is unowned or
    already owned by this account. Returns the row, or None if the guard failed."""
    async with conn.cursor() as cur:
        await cur.execute(
            "UPDATE address SET owner_account_id = %s::uuid, alias = COALESCE(%s, alias) "
            "WHERE code = %s AND (owner_account_id IS NULL OR owner_account_id = %s::uuid) "
            "RETURNING id",
            (account_id, alias, code, account_id),
        )
        return await cur.fetchone()


async def exists_by_olc(conn, olc: str) -> bool:
    async with conn.cursor() as cur:
        await cur.execute("SELECT 1 FROM address WHERE olc = %s LIMIT 1", (olc,))
        return (await cur.fetchone()) is not None


async def insert_imported(
    conn, code: str, olc: str, geohash: str, row: dict, source: str, confidence: float
) -> None:
    """Insert a bootstrapped/imported address with provenance + a source confidence."""
    async with conn.transaction():
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO address "
                "(code, olc, alias, lat, lng, geohash, state, lga, confidence, status, source) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'unverified', %s) RETURNING id",
                (
                    code,
                    olc,
                    row.get("alias"),
                    row["lat"],
                    row["lng"],
                    geohash,
                    row.get("state"),
                    row.get("lga"),
                    confidence,
                    source,
                ),
            )
            address_id = (await cur.fetchone())["id"]
            if row.get("landmark") or row.get("building_desc"):
                await cur.execute(
                    "INSERT INTO address_metadata (address_id, landmark, building_desc) "
                    "VALUES (%s, %s, %s)",
                    (address_id, row.get("landmark"), row.get("building_desc")),
                )


async def bump_confidence(conn, address_id, delta: float) -> None:
    """Nudge an address's confidence up (capped at 1.0) — e.g. after a
    successful delivery to it (the feedback loop)."""
    await conn.execute(
        "UPDATE address SET confidence = LEAST(1.0, confidence + %s) WHERE id = %s",
        (delta, address_id),
    )


async def touch_verification(conn, code: str, confidence: float, verified_at) -> None:
    """Record a successful (re)verification: bump the count, refresh the
    timestamp, update running confidence, and mark the address verified."""
    await conn.execute(
        "UPDATE address SET last_verified_at = %s, verification_count = verification_count + 1, "
        "confidence = %s, status = 'verified' WHERE code = %s",
        (verified_at, confidence, code),
    )
