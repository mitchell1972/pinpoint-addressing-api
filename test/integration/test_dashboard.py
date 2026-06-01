async def test_dashboard_index_is_served(client):
    r = await client.get("/dashboard/")
    assert r.status_code == 200
    assert "Dispatch Dashboard" in r.text
    assert 'data-testid="search-input"' in r.text


async def test_dashboard_script_is_served(client):
    r = await client.get("/dashboard/app.js")
    assert r.status_code == 200
    assert "/v1/geocode" in r.text
