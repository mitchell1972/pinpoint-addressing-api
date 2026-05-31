async def test_billable_call_records_exactly_one_usage_event(client, test_auth):
    before = (await client.get("/v1/usage", headers=test_auth)).json()
    assert before["total_units"] == 0

    g = await client.post(
        "/v1/geocode",
        headers=test_auth,
        json={"query": "ikeja city mall", "area": {"state": "Lagos", "lga": "Ikeja"}},
    )
    assert g.status_code == 200
    # Rate-limit contract is surfaced (enforcement is a documented TODO).
    assert "X-RateLimit-Limit" in g.headers

    after = (await client.get("/v1/usage", headers=test_auth)).json()
    assert after["total_units"] == 1
    assert after["total_calls"] == 1
    assert after["by_endpoint"][0]["endpoint"] == "/v1/geocode"


async def test_usage_endpoint_is_not_billable(client, test_auth):
    # Reading usage must not meter itself.
    await client.get("/v1/usage", headers=test_auth)
    await client.get("/v1/usage", headers=test_auth)
    after = (await client.get("/v1/usage", headers=test_auth)).json()
    assert after["total_units"] == 0
