async def log_request(conn, account_id, method: str, path: str, status: int) -> None:
    await conn.execute(
        "INSERT INTO request_log (account_id, method, path, status) VALUES (%s::uuid, %s, %s, %s)",
        (account_id, method, path, status),
    )


async def purge_request_logs(conn, older_than_days: int) -> int:
    """Apply the retention policy: drop request logs older than N days."""
    async with conn.cursor() as cur:
        await cur.execute(
            "DELETE FROM request_log WHERE ts < now() - make_interval(days => %s)",
            (older_than_days,),
        )
        return cur.rowcount
