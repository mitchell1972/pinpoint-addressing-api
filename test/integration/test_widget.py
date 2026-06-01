async def test_widget_demo_is_served(client):
    r = await client.get("/widget/demo.html")
    assert r.status_code == 200
    assert 'id="pinpoint-widget"' in r.text


async def test_widget_script_is_served(client):
    r = await client.get("/widget/widget.js")
    assert r.status_code == 200
    assert "/v1/geocode" in r.text
    assert "pinpoint:selected" in r.text
