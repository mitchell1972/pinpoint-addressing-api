_GET = """
SELECT response_status, response_body, response_media_type
FROM idempotency_key
WHERE scope = %s AND idem_key = %s
"""

_PUT = """
INSERT INTO idempotency_key
    (scope, idem_key, method, path, response_status, response_body, response_media_type)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (scope, idem_key) DO NOTHING
"""


async def get(conn, scope: str, key: str) -> dict | None:
    async with conn.cursor() as cur:
        await cur.execute(_GET, (scope, key))
        return await cur.fetchone()


async def put(
    conn,
    scope: str,
    key: str,
    method: str,
    path: str,
    status: int,
    body: str,
    media_type: str,
) -> None:
    # ON CONFLICT DO NOTHING: if two identical requests race, the first stored
    # response wins and the second insert is a no-op.
    await conn.execute(_PUT, (scope, key, method, path, status, body, media_type))
