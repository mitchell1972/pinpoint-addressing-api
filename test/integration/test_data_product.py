async def test_non_admin_cannot_read_coverage(client, test_auth):
    r = await client.get("/v1/data/coverage", headers=test_auth)
    assert r.status_code == 403


async def test_coverage_is_aggregated_and_anonymised(client, admin_auth):
    r = await client.get("/v1/data/coverage", headers=admin_auth)
    assert r.status_code == 200
    rows = r.json()["coverage"]
    assert rows  # seeded fixtures span several LGAs
    # Only aggregate fields — no personal data (contact, alias, exact code) leaks.
    assert set(rows[0].keys()) == {"lga", "total", "verified", "avg_confidence"}
