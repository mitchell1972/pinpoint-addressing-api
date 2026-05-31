async def test_missing_key_is_401(client):
    r = await client.get("/v1/usage")
    assert r.status_code == 401


async def test_malformed_key_is_401(client):
    r = await client.get("/v1/usage", headers={"Authorization": "Bearer not-a-real-key"})
    assert r.status_code == 401


async def test_test_key_is_scoped_test(client, test_auth):
    r = await client.get("/v1/usage", headers=test_auth)
    assert r.status_code == 200
    assert r.json()["env"] == "test"


async def test_live_key_is_scoped_live(client, live_auth):
    r = await client.get("/v1/usage", headers=live_auth)
    assert r.status_code == 200
    assert r.json()["env"] == "live"
