async def test_deliveries_require_auth(client):
    r = await client.post("/v1/deliveries", json={"code": "PIN-VIC-002", "status": "delivered"})
    assert r.status_code == 401


async def test_record_unknown_code_is_404(client, test_auth):
    r = await client.post(
        "/v1/deliveries", headers=test_auth, json={"code": "PIN-NONE-00", "status": "delivered"}
    )
    assert r.status_code == 404


async def test_summary_counts_and_rates(client, test_auth):
    deliveries = [
        ("PIN-VIC-002", "delivered", 120),
        ("PIN-IKY-001", "delivered", 90),
        ("PIN-LEK-003", "delivered", 150),
        ("PIN-OSH-008", "failed", None),
    ]
    for code, status, ttl in deliveries:
        payload = {"code": code, "status": status}
        if ttl is not None:
            payload["time_to_locate_seconds"] = ttl
        assert (
            await client.post("/v1/deliveries", headers=test_auth, json=payload)
        ).status_code == 201

    s = (await client.get("/v1/analytics/summary", headers=test_auth)).json()
    assert s["total"] == 4
    assert s["delivered"] == 3
    assert s["failed"] == 1
    assert s["failed_rate"] == round(1 / 4, 3)
    assert s["avg_time_to_locate_seconds"] == round((120 + 90 + 150) / 3, 1)


async def test_hotspots_group_by_lga(client, test_auth):
    for code, status in [
        ("PIN-OSH-008", "failed"),
        ("PIN-OSH-016", "failed"),
        ("PIN-VIC-002", "delivered"),
    ]:
        await client.post(
            "/v1/deliveries", headers=test_auth, json={"code": code, "status": status}
        )

    hotspots = (await client.get("/v1/analytics/hotspots", headers=test_auth)).json()["hotspots"]
    oshodi = [h for h in hotspots if h["lga"] == "Oshodi-Isolo"]
    assert oshodi and oshodi[0]["failed"] == 2


async def test_successful_delivery_bumps_confidence(client, test_auth):
    before = (
        await client.post("/v1/verify", headers=test_auth, json={"code": "PIN-YAB-004"})
    ).json()
    await client.post(
        "/v1/deliveries",
        headers=test_auth,
        json={"code": "PIN-YAB-004", "status": "delivered", "time_to_locate_seconds": 60},
    )
    after = (
        await client.post("/v1/verify", headers=test_auth, json={"code": "PIN-YAB-004"})
    ).json()
    assert after["confidence"] > before["confidence"]
