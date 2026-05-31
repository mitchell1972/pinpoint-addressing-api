async def test_usage_shape_starts_empty(client, test_auth):
    r = await client.get("/v1/usage", headers=test_auth)
    assert r.status_code == 200
    body = r.json()
    assert {"account_id", "env", "total_units", "total_calls", "by_endpoint"} <= body.keys()
    assert body["total_units"] == 0
    assert body["total_calls"] == 0
    assert body["by_endpoint"] == []
