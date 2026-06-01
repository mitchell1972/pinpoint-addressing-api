async def test_non_admin_cannot_manage_accounts(client, test_auth):
    r = await client.post("/v1/accounts", headers=test_auth, json={"name": "X", "type": "merchant"})
    assert r.status_code == 403


async def test_admin_creates_account_and_issues_working_key(client, admin_auth):
    acc = await client.post(
        "/v1/accounts",
        headers=admin_auth,
        json={"name": "Jumia", "type": "merchant", "tier": "pro"},
    )
    assert acc.status_code == 201
    account_id = acc.json()["id"]

    issued = await client.post(
        f"/v1/accounts/{account_id}/keys",
        headers=admin_auth,
        json={"env": "test", "scope": "read", "rate_limit": 30},
    )
    assert issued.status_code == 201
    new_key = issued.json()["key"]
    assert new_key.startswith("pk_test_")

    # the freshly issued key actually authenticates
    g = await client.post(
        "/v1/geocode",
        headers={"Authorization": f"Bearer {new_key}"},
        json={"query": "ikeja city mall"},
    )
    assert g.status_code == 200


async def test_revoked_key_stops_working(client, admin_auth):
    acc = await client.post(
        "/v1/accounts", headers=admin_auth, json={"name": "Temp", "type": "courier"}
    )
    account_id = acc.json()["id"]
    issued = await client.post(
        f"/v1/accounts/{account_id}/keys", headers=admin_auth, json={"env": "test"}
    )
    key_id, new_key = issued.json()["id"], issued.json()["key"]
    auth = {"Authorization": f"Bearer {new_key}"}

    assert (
        await client.post("/v1/geocode", headers=auth, json={"query": "ikeja"})
    ).status_code == 200

    revoked = await client.post(f"/v1/keys/{key_id}/revoke", headers=admin_auth)
    assert revoked.status_code == 204

    assert (
        await client.post("/v1/geocode", headers=auth, json={"query": "ikeja"})
    ).status_code == 401


async def test_issue_key_for_missing_account_is_404(client, admin_auth):
    r = await client.post(
        "/v1/accounts/00000000-0000-0000-0000-000000000000/keys",
        headers=admin_auth,
        json={"env": "test"},
    )
    assert r.status_code == 404
