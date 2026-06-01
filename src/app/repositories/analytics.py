async def record_delivery(conn, address_id, account_id, status, reason, ttl) -> str:
    async with conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO delivery_event (address_id, account_id, status, reason, time_to_locate_seconds) "
            "VALUES (%s, %s::uuid, %s, %s, %s) RETURNING id",
            (address_id, account_id, status, reason, ttl),
        )
        return (await cur.fetchone())["id"]


async def summary(conn, account_id) -> dict:
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT count(*) AS total, "
            "count(*) FILTER (WHERE status = 'delivered') AS delivered, "
            "count(*) FILTER (WHERE status = 'failed') AS failed, "
            "avg(time_to_locate_seconds) FILTER (WHERE status = 'delivered') AS avg_ttl "
            "FROM delivery_event WHERE account_id = %s::uuid",
            (account_id,),
        )
        return await cur.fetchone()


async def hotspots(conn, account_id) -> list[dict]:
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT a.lga, count(*) AS total, "
            "count(*) FILTER (WHERE d.status = 'failed') AS failed "
            "FROM delivery_event d JOIN address a ON a.id = d.address_id "
            "WHERE d.account_id = %s::uuid "
            "GROUP BY a.lga ORDER BY failed DESC, total DESC",
            (account_id,),
        )
        return await cur.fetchall()
