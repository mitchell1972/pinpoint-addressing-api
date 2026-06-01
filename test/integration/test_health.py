async def test_health_is_ok(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_ready_when_db_reachable(client):
    r = await client.get("/ready")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"
