async def test_geocode_requires_auth(client):
    r = await client.post("/v1/geocode", json={"query": "silverbird"})
    assert r.status_code == 401


async def test_geocode_rejects_empty_body(client, test_auth):
    r = await client.post("/v1/geocode", headers=test_auth, json={})
    assert r.status_code == 422


async def test_geocode_returns_documented_shape(client, test_auth):
    r = await client.post(
        "/v1/geocode",
        headers=test_auth,
        json={
            "query": "silverbird galleria ahmadu bello way",
            "area": {"state": "Lagos", "lga": "Eti-Osa"},
            "limit": 3,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert {"results", "request_id", "units"} <= body.keys()
    assert body["request_id"].startswith("req_")
    assert body["units"] == 1
    assert isinstance(body["results"], list) and body["results"]

    top = body["results"][0]
    assert {"code", "lat", "lng", "confidence", "landmark", "verified"} <= top.keys()
    assert top["code"] == "PIN-VIC-002"
    assert top["verified"] is True
