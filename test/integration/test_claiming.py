async def test_creator_can_claim_and_rename(client, test_auth):
    created = await client.post(
        "/v1/addresses", headers=test_auth, json={"lat": 6.45, "lng": 3.40, "landmark": "Shop"}
    )
    code = created.json()["code"]

    claimed = await client.post(
        f"/v1/addresses/{code}/claim", headers=test_auth, json={"alias": "My main shop"}
    )
    assert claimed.status_code == 200
    assert claimed.json()["alias"] == "My main shop"


async def test_cannot_claim_another_accounts_address(client, test_auth, admin_auth):
    # Account A (demo) creates an address — it is owned by A.
    created = await client.post(
        "/v1/addresses", headers=test_auth, json={"lat": 6.46, "lng": 3.41, "landmark": "A's shop"}
    )
    code = created.json()["code"]

    # Spin up a separate account B with its own key.
    acc_b = await client.post(
        "/v1/accounts", headers=admin_auth, json={"name": "B Ltd", "type": "merchant"}
    )
    key_b = (
        await client.post(
            f"/v1/accounts/{acc_b.json()['id']}/keys", headers=admin_auth, json={"env": "test"}
        )
    ).json()["key"]

    # B tries to claim A's address -> forbidden.
    blocked = await client.post(
        f"/v1/addresses/{code}/claim",
        headers={"Authorization": f"Bearer {key_b}"},
        json={"alias": "mine now"},
    )
    assert blocked.status_code == 403


async def test_claim_unknown_code_is_404(client, test_auth):
    r = await client.post("/v1/addresses/PIN-NONE-00/claim", headers=test_auth, json={"alias": "x"})
    assert r.status_code == 404
