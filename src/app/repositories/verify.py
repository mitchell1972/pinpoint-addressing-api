_INSERT_VERIFICATION = """
INSERT INTO verification (address_id, method, score, verifier)
SELECT id, %s, %s, %s FROM address WHERE code = %s
RETURNING id
"""


async def create_verification(conn, code: str, method: str, score: float, verifier: str) -> str:
    async with conn.cursor() as cur:
        await cur.execute(_INSERT_VERIFICATION, (method, score, verifier, code))
        return (await cur.fetchone())["id"]
