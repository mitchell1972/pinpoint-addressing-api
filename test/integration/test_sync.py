async def test_sync_requires_auth(client):
    r = await client.post(
        "/v1/sync",
        json={
            "captures": [
                {"capture_id": "33333333-3333-3333-3333-333333333333", "lat": 6.5, "lng": 3.3}
            ]
        },
    )
    assert r.status_code == 401


async def test_sync_creates_then_dedupes_by_capture_id(client, test_auth):
    captures = [
        {
            "capture_id": "11111111-1111-1111-1111-111111111111",
            "lat": 6.50,
            "lng": 3.36,
            "landmark": "Cap A",
        },
        {
            "capture_id": "22222222-2222-2222-2222-222222222222",
            "lat": 6.51,
            "lng": 3.37,
            "landmark": "Cap B",
        },
    ]
    first = await client.post("/v1/sync", headers=test_auth, json={"captures": captures})
    assert first.status_code == 201
    res1 = first.json()["results"]
    assert all(x["status"] == "created" for x in res1)
    codes = {x["capture_id"]: x["code"] for x in res1}

    # Re-syncing the same queue (e.g. after a flaky connection) must not duplicate.
    second = await client.post("/v1/sync", headers=test_auth, json={"captures": captures})
    res2 = second.json()["results"]
    assert all(x["status"] == "duplicate" for x in res2)
    assert {x["capture_id"]: x["code"] for x in res2} == codes
