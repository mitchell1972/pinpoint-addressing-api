_FIND_ACTIVE_KEY = """
SELECT k.id AS api_key_id, k.env, k.scope, k.rate_limit,
       a.id AS account_id, a.type AS account_type
FROM api_key k
JOIN account a ON a.id = k.account_id
WHERE k.key_hash = %s AND k.status = 'active' AND a.status = 'active'
"""


async def find_active_key(conn, key_hash: str) -> dict | None:
    async with conn.cursor() as cur:
        await cur.execute(_FIND_ACTIVE_KEY, (key_hash,))
        return await cur.fetchone()
