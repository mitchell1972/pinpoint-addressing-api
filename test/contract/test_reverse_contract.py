async def test_reverse_requires_auth(client):
    r = await client.post("/v1/reverse", json={"lat": 6.4281, "lng": 3.4219})
    assert r.status_code == 401


async def test_reverse_rejects_out_of_range_coords(client, test_auth):
    r = await client.post("/v1/reverse", headers=test_auth, json={"lat": 200, "lng": 3.4})
    assert r.status_code == 422


async def test_reverse_finds_nearest_verified_address(client, test_auth):
    # Exactly the seeded Victoria Island coordinates.
    r = await client.post(
        "/v1/reverse",
        headers=test_auth,
        json={"lat": 6.4281, "lng": 3.4219, "limit": 1},
    )
    assert r.status_code == 200
    results = r.json()["results"]
    assert results and results[0]["code"] == "PIN-VIC-002"
    assert results[0]["confidence"] >= 0.99  # zero distance -> ~1.0
