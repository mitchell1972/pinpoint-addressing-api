async def test_verify_requires_auth(client):
    r = await client.post("/v1/verify", json={"code": "PIN-VIC-002"})
    assert r.status_code == 401


async def test_verify_requires_a_target(client, test_auth):
    # Neither code nor lat/lng -> schema validator rejects.
    r = await client.post("/v1/verify", headers=test_auth, json={})
    assert r.status_code == 422


async def test_verify_by_code_basic(client, test_auth):
    r = await client.post("/v1/verify", headers=test_auth, json={"code": "PIN-VIC-002"})
    assert r.status_code == 200
    body = r.json()
    assert body["exists"] is True
    assert body["code"] == "PIN-VIC-002"
    assert body["mode"] == "basic"
    assert body["confidence"] >= 0.9
    assert body["verification_id"] is None  # basic mode writes no record


async def test_verify_by_coordinates(client, test_auth):
    # Exactly the seeded Victoria Island point.
    r = await client.post("/v1/verify", headers=test_auth, json={"lat": 6.4281, "lng": 3.4219})
    assert r.status_code == 200
    body = r.json()
    assert body["exists"] is True
    assert body["code"] == "PIN-VIC-002"


async def test_verify_unknown_code_does_not_exist(client, test_auth):
    r = await client.post("/v1/verify", headers=test_auth, json={"code": "PIN-NONE-99"})
    assert r.status_code == 200
    body = r.json()
    assert body["exists"] is False
    assert body["confidence"] == 0.0


async def test_verify_kyc_mode_writes_evidence_reference(client, test_auth):
    r = await client.post(
        "/v1/verify", headers=test_auth, json={"code": "PIN-VIC-002", "mode": "kyc"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "kyc"
    assert body["verification_id"] is not None
    assert body["evidence_ref"].startswith("ver_")
