_INSERT_USAGE = """
INSERT INTO usage_event (account_id, endpoint, units, cost)
VALUES (%s, %s, %s, %s)
"""

_USAGE_BY_ENDPOINT = """
SELECT endpoint, sum(units)::int AS units, count(*)::int AS calls
FROM usage_event
WHERE account_id = %s
GROUP BY endpoint
ORDER BY endpoint
"""


async def record_usage(conn, account_id: str, endpoint: str, units: int = 1, cost: int = 0) -> None:
    await conn.execute(_INSERT_USAGE, (account_id, endpoint, units, cost))


async def usage_by_endpoint(conn, account_id: str) -> list[dict]:
    async with conn.cursor() as cur:
        await cur.execute(_USAGE_BY_ENDPOINT, (account_id,))
        return await cur.fetchall()
