import pytest


async def test_create_then_resolve_by_code(client, test_auth):
    r = await client.post(
        "/v1/addresses",
        headers=test_auth,
        json={
            "lat": 6.4470, "lng": 3.4730,
            "alias": "My shop",
            "landmark": "Beside Lekki Phase 1 gate",
            "state": "Lagos", "lga": "Eti-Osa",
        },
    )
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["code"].startswith("PIN-")
    assert created["olc"]          # Plus Code computed
    assert created["geohash"]      # geohash computed
    assert created["status"] == "unverified"

    r2 = await client.get(f"/v1/addresses/{created['code']}", headers=test_auth)
    assert r2.status_code == 200
    got = r2.json()
    assert got["lat"] == pytest.approx(6.4470)
    assert got["lng"] == pytest.approx(3.4730)
    assert got["landmark"] == "Beside Lekki Phase 1 gate"


async def test_create_then_reverse_finds_it(client, test_auth):
    r = await client.post(
        "/v1/addresses",
        headers=test_auth,
        json={"lat": 6.6018, "lng": 3.3515, "landmark": "New warehouse, Agege"},
    )
    code = r.json()["code"]

    rr = await client.post(
        "/v1/reverse",
        headers=test_auth,
        json={"lat": 6.6018, "lng": 3.3515, "limit": 1},
    )
    assert rr.status_code == 200
    assert rr.json()["results"][0]["code"] == code


async def test_resolve_unknown_code_is_404(client, test_auth):
    r = await client.get("/v1/addresses/PIN-NONE-99", headers=test_auth)
    assert r.status_code == 404
