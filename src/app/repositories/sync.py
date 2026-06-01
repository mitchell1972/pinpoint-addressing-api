async def find_capture(conn, capture_id: str) -> dict | None:
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT a.code FROM captured_address c JOIN address a ON a.id = c.address_id "
            "WHERE c.capture_id = %s::uuid",
            (capture_id,),
        )
        return await cur.fetchone()


async def record_capture(conn, capture_id: str, address_id, account_id: str) -> None:
    await conn.execute(
        "INSERT INTO captured_address (capture_id, address_id, account_id) "
        "VALUES (%s::uuid, %s, %s::uuid) ON CONFLICT (capture_id) DO NOTHING",
        (capture_id, address_id, account_id),
    )
