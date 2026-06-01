async def test_verify_requires_auth(client):
    r = await client.post("/v1/verify", json={"code": "PIN-VIC-002"})
    assert r.status_code == 401


async def test_verify_requires_a_target(client, test_auth):
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
    assert body["freshness"] >= 0.99  # freshly seeded
    assert body["stale"] is False
    assert body["verification_id"] is None  # basic mode writes nothing


async def test_verify_by_coordinates(client, test_auth):
    r = await client.post("/v1/verify", headers=test_auth, json={"lat": 6.4281, "lng": 3.4219})
    assert r.status_code == 200
    assert r.json()["code"] == "PIN-VIC-002"


async def test_verify_unknown_code_does_not_exist(client, test_auth):
    r = await client.post("/v1/verify", headers=test_auth, json={"code": "PIN-NONE-99"})
    assert r.status_code == 200
    body = r.json()
    assert body["exists"] is False
    assert body["confidence"] == 0.0
    assert body["stale"] is True


async def test_verify_kyc_mode_writes_evidence_reference(client, test_auth):
    r = await client.post(
        "/v1/verify",
        headers=test_auth,
        json={"code": "PIN-VIC-002", "mode": "kyc", "device": "rider-app/1.0"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "kyc"
    assert body["verification_id"] is not None
    assert body["evidence_ref"] is not None
    assert len(body["evidence_ref"]) == 64  # sha256 hex of the ledger entry


async def test_kyc_builds_tamper_evident_ledger(client, test_auth):
    from app.core.db import open_pool
    from app.repositories import verify as verify_repo

    for code in ("PIN-VIC-002", "PIN-IKY-001"):
        r = await client.post(
            "/v1/verify",
            headers=test_auth,
            json={"code": code, "mode": "kyc", "device": "rider-app/1.0"},
        )
        assert r.status_code == 200

    pool = await open_pool()
    async with pool.connection() as conn:
        report = await verify_repo.integrity(conn)
    assert report["ok"] is True
    assert report["entries"] == 2

    # Editing a past entry must break the chain.
    async with pool.connection() as conn:
        await conn.execute(
            "UPDATE verification SET score = 0.01 WHERE seq = (SELECT min(seq) FROM verification)"
        )
        broken = await verify_repo.integrity(conn)
    assert broken["ok"] is False
    assert broken["broken_seq"] is not None
