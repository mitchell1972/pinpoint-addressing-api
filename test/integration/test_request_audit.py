async def test_v1_requests_are_logged(client, test_auth):
    from app.core.db import open_pool

    await client.post("/v1/geocode", headers=test_auth, json={"query": "ikeja city mall"})

    pool = await open_pool()
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            "SELECT count(*)::int AS n FROM request_log WHERE path = %s", ("/v1/geocode",)
        )
        n = (await cur.fetchone())["n"]
    assert n >= 1


async def test_retention_purge_drops_old_logs(client, test_auth):
    from app.core.db import open_pool
    from app.repositories import audit as audit_repo

    pool = await open_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO request_log (method, path, status, ts) "
                "VALUES ('GET', '/v1/old', 200, now() - make_interval(days => 400))"
            )
            await cur.execute(
                "INSERT INTO request_log (method, path, status) VALUES ('GET', '/v1/new', 200)"
            )
        deleted = await audit_repo.purge_request_logs(conn, 30)
        async with conn.cursor() as cur:
            await cur.execute("SELECT count(*)::int AS n FROM request_log WHERE path = '/v1/old'")
            old_n = (await cur.fetchone())["n"]
            await cur.execute("SELECT count(*)::int AS n FROM request_log WHERE path = '/v1/new'")
            new_n = (await cur.fetchone())["n"]

    assert deleted >= 1
    assert old_n == 0
    assert new_n >= 1
