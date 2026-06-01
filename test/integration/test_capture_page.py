async def test_capture_page_is_served(client):
    r = await client.get("/capture/")
    assert r.status_code == 200
    assert 'data-testid="queue-btn"' in r.text


async def test_capture_manifest_is_served(client):
    r = await client.get("/capture/manifest.json")
    assert r.status_code == 200
    assert "Field Capture" in r.text
