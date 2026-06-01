async def test_non_admin_cannot_import(client, test_auth):
    r = await client.post(
        "/v1/import", headers=test_auth, json={"rows": [{"lat": 7.0, "lng": 4.0}], "source": "osm"}
    )
    assert r.status_code == 403


async def test_admin_imports_then_dedupes_by_plus_code(client, admin_auth):
    rows = [
        {
            "lat": 7.10,
            "lng": 4.10,
            "landmark": "Importtest Plaza Alpha",
            "state": "Lagos",
            "lga": "Ikeja",
        },
        {
            "lat": 7.20,
            "lng": 4.20,
            "landmark": "Importtest Market Beta",
            "state": "Lagos",
            "lga": "Ikeja",
        },
    ]
    first = await client.post(
        "/v1/import", headers=admin_auth, json={"rows": rows, "source": "osm"}
    )
    assert first.status_code == 201
    assert first.json() == {"inserted": 2, "skipped": 0}

    # Re-importing the same points is a no-op (deduped by Plus Code).
    again = await client.post(
        "/v1/import", headers=admin_auth, json={"rows": rows, "source": "osm"}
    )
    assert again.json() == {"inserted": 0, "skipped": 2}


async def test_imported_address_is_searchable(client, admin_auth):
    await client.post(
        "/v1/import",
        headers=admin_auth,
        json={
            "rows": [{"lat": 7.33, "lng": 4.44, "landmark": "Importtest Beacon Tower"}],
            "source": "osm",
        },
    )
    g = await client.post(
        "/v1/geocode", headers=admin_auth, json={"query": "importtest beacon tower"}
    )
    assert g.status_code == 200
    landmarks = [res.get("landmark") for res in g.json()["results"]]
    assert "Importtest Beacon Tower" in landmarks
