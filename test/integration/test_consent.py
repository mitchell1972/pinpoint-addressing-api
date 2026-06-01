async def test_consent_recorded_on_create(client, test_auth):
    r = await client.post(
        "/v1/addresses",
        headers=test_auth,
        json={"lat": 6.45, "lng": 3.40, "landmark": "Consented shop", "consent": True},
    )
    assert r.status_code == 201
    assert r.json()["consent"] is True

    got = await client.get(f"/v1/addresses/{r.json()['code']}", headers=test_auth)
    assert got.json()["consent"] is True


async def test_consent_defaults_false(client, test_auth):
    r = await client.post(
        "/v1/addresses",
        headers=test_auth,
        json={"lat": 6.46, "lng": 3.41, "landmark": "No consent"},
    )
    assert r.json()["consent"] is False
