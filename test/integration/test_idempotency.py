async def test_same_key_replays_and_creates_once(client, test_auth):
    headers = {**test_auth, "Idempotency-Key": "create-warehouse-001"}
    body = {"lat": 6.6018, "lng": 3.3515, "landmark": "Idempotency test warehouse"}

    first = await client.post("/v1/addresses", headers=headers, json=body)
    assert first.status_code == 201
    code = first.json()["code"]

    second = await client.post("/v1/addresses", headers=headers, json=body)
    assert second.status_code == 201
    assert second.json()["code"] == code  # same response replayed
    assert second.headers.get("Idempotent-Replay") == "true"

    # Only one address was actually created at those coordinates.
    rev = await client.post(
        "/v1/reverse",
        headers=test_auth,
        json={"lat": 6.6018, "lng": 3.3515, "limit": 5, "radius_m": 300},
    )
    assert len(rev.json()["results"]) == 1


async def test_without_key_there_is_no_dedupe(client, test_auth):
    body = {"lat": 6.6200, "lng": 3.3000, "landmark": "No-key warehouse"}
    first = await client.post("/v1/addresses", headers=test_auth, json=body)
    second = await client.post("/v1/addresses", headers=test_auth, json=body)
    assert first.status_code == second.status_code == 201
    assert first.json()["code"] != second.json()["code"]  # two distinct addresses


async def test_key_is_scoped_per_credential(client, test_auth, live_auth):
    # Same key, different credentials -> no cross-caller replay.
    body = {"lat": 6.4800, "lng": 3.3600, "landmark": "Scoped warehouse"}
    a = await client.post(
        "/v1/addresses", headers={**test_auth, "Idempotency-Key": "shared"}, json=body
    )
    b = await client.post(
        "/v1/addresses", headers={**live_auth, "Idempotency-Key": "shared"}, json=body
    )
    assert a.json()["code"] != b.json()["code"]
