from app.core.security import hash_key


async def create_account(conn, name: str, type_: str, tier: str) -> dict:
    async with conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO account (name, type, tier) VALUES (%s, %s, %s) "
            "RETURNING id, name, type, tier, status",
            (name, type_, tier),
        )
        return await cur.fetchone()


async def account_exists(conn, account_id) -> bool:
    async with conn.cursor() as cur:
        await cur.execute("SELECT 1 FROM account WHERE id = %s", (account_id,))
        return (await cur.fetchone()) is not None


async def create_api_key(
    conn, account_id, raw_key: str, env: str, scope: str, rate_limit: int
) -> dict:
    async with conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO api_key (account_id, key_hash, key_prefix, env, scope, rate_limit) "
            "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id, key_prefix, env, scope, rate_limit",
            (account_id, hash_key(raw_key), raw_key[:16], env, scope, rate_limit),
        )
        return await cur.fetchone()


async def revoke_key(conn, key_id) -> bool:
    async with conn.cursor() as cur:
        await cur.execute(
            "UPDATE api_key SET status = 'revoked' WHERE id = %s AND status = 'active' RETURNING id",
            (key_id,),
        )
        return (await cur.fetchone()) is not None
