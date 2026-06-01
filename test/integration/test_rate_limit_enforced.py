async def test_exceeding_the_limit_returns_429(client, limit_auth):
    # limit_auth is seeded with a per-minute limit of 3.
    for _ in range(3):
        ok = await client.post("/v1/geocode", headers=limit_auth, json={"query": "ikeja city mall"})
        assert ok.status_code == 200

    blocked = await client.post(
        "/v1/geocode", headers=limit_auth, json={"query": "ikeja city mall"}
    )
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers
    assert blocked.headers["X-RateLimit-Remaining"] == "0"


async def test_remaining_header_counts_down(client, test_auth):
    r = await client.post("/v1/geocode", headers=test_auth, json={"query": "ikeja city mall"})
    assert r.status_code == 200
    # test_auth has a limit of 60; after one call, 59 remain.
    assert r.headers["X-RateLimit-Limit"] == "60"
    assert r.headers["X-RateLimit-Remaining"] == "59"
