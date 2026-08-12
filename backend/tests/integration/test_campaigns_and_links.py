

async def _register_and_login(client, email="owner@example.com", password="StrongPass123"):
    resp = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password, "full_name": "Owner"}
    )
    assert resp.status_code == 201
    return resp.json()


async def _create_campaign(client, name="Summer Sale"):
    resp = await client.post("/api/v1/campaigns", json={"name": name, "description": "desc"})
    assert resp.status_code == 201
    return resp.json()


async def test_create_and_list_campaigns(client):
    await _register_and_login(client)
    campaign = await _create_campaign(client)
    assert campaign["name"] == "Summer Sale"
    assert campaign["status"] == "ACTIVE"

    list_resp = await client.get("/api/v1/campaigns")
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == campaign["id"]


async def test_campaign_idor_protection(client, db_session):
    await _register_and_login(client, email="owner@example.com")
    campaign = await _create_campaign(client)
    await client.post("/api/v1/auth/logout")

    await _register_and_login(client, email="attacker@example.com")
    resp = await client.get(f"/api/v1/campaigns/{campaign['id']}")
    assert resp.status_code == 404  # not leaked as 403 either — appears not to exist


async def test_create_link_with_custom_alias(client):
    await _register_and_login(client)
    campaign = await _create_campaign(client)

    resp = await client.post(
        "/api/v1/links",
        json={
            "target_url": "https://example.com/landing",
            "campaign_id": campaign["id"],
            "custom_alias": "summer2026",
            "requires_consent": False,
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["short_code"] == "summer2026"
    assert body["short_url"].endswith("/t/summer2026")


async def test_create_link_rejects_reserved_alias(client):
    await _register_and_login(client)
    resp = await client.post(
        "/api/v1/links", json={"target_url": "https://example.com", "custom_alias": "admin"}
    )
    assert resp.status_code == 422


async def test_create_link_rejects_duplicate_alias(client):
    await _register_and_login(client)
    body = {"target_url": "https://example.com", "custom_alias": "myalias"}
    resp1 = await client.post("/api/v1/links", json=body)
    assert resp1.status_code == 201
    resp2 = await client.post("/api/v1/links", json=body)
    assert resp2.status_code == 409


async def test_create_link_rejects_non_https_scheme(client):
    await _register_and_login(client)
    resp = await client.post("/api/v1/links", json={"target_url": "javascript:alert(1)"})
    assert resp.status_code == 422


async def test_create_link_rejects_internal_targets(client):
    await _register_and_login(client)
    resp = await client.post("/api/v1/links", json={"target_url": "http://169.254.169.254/latest/meta-data"})
    assert resp.status_code == 422


async def test_create_link_without_alias_autogenerates_code(client):
    await _register_and_login(client)
    resp = await client.post("/api/v1/links", json={"target_url": "https://example.com"})
    assert resp.status_code == 201
    assert len(resp.json()["short_code"]) == 7


async def test_link_idor_protection(client):
    await _register_and_login(client, email="owner2@example.com")
    resp = await client.post(
        "/api/v1/links", json={"target_url": "https://example.com", "custom_alias": "victimlink"}
    )
    link_id = resp.json()["id"]
    await client.post("/api/v1/auth/logout")

    await _register_and_login(client, email="attacker2@example.com")
    get_resp = await client.get(f"/api/v1/links/{link_id}")
    assert get_resp.status_code == 404

    update_resp = await client.patch(f"/api/v1/links/{link_id}", json={"description": "hacked"})
    assert update_resp.status_code == 404

    delete_resp = await client.delete(f"/api/v1/links/{link_id}")
    assert delete_resp.status_code == 404


async def test_redirect_without_gate_records_visit_and_redirects(client):
    await _register_and_login(client)
    resp = await client.post(
        "/api/v1/links",
        json={"target_url": "https://example.com/target", "custom_alias": "nogatelink", "requires_consent": False},
    )
    assert resp.status_code == 201

    redirect_resp = await client.get("/t/nogatelink", follow_redirects=False)
    assert redirect_resp.status_code == 302
    assert redirect_resp.headers["location"] == "https://example.com/target"


async def test_redirect_unknown_code_sends_to_not_found_page(client):
    resp = await client.get("/t/does-not-exist", follow_redirects=False)
    assert resp.status_code == 302
    assert "not-found" in resp.headers["location"]


async def test_redirect_with_consent_required_goes_to_gate(client):
    await _register_and_login(client)
    await client.post(
        "/api/v1/links",
        json={"target_url": "https://example.com/target", "custom_alias": "consentlink", "requires_consent": True},
    )
    resp = await client.get("/t/consentlink", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"].endswith("/t/consentlink/gate")


async def test_meta_and_resolve_flow_with_consent(client):
    await _register_and_login(client)
    await client.post(
        "/api/v1/links",
        json={"target_url": "https://example.com/target", "custom_alias": "metalink", "requires_consent": True},
    )
    await client.post("/api/v1/auth/logout")

    meta_resp = await client.get("/api/v1/t/metalink/meta")
    assert meta_resp.status_code == 200
    assert meta_resp.json() == {"needs_password": False, "needs_consent": True}

    resolve_resp = await client.post("/api/v1/t/metalink/resolve", json={"consent": True})
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["target_url"] == "https://example.com/target"


async def test_resolve_with_consent_rejected_still_redirects_minimal_data(client):
    await _register_and_login(client)
    await client.post(
        "/api/v1/links",
        json={"target_url": "https://example.com/target", "custom_alias": "rejectlink", "requires_consent": True},
    )
    await client.post("/api/v1/auth/logout")

    resolve_resp = await client.post("/api/v1/t/rejectlink/resolve", json={"consent": False})
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["target_url"] == "https://example.com/target"


async def test_password_protected_link_requires_correct_password(client):
    await _register_and_login(client)
    create_resp = await client.post(
        "/api/v1/links",
        json={
            "target_url": "https://example.com/secret",
            "custom_alias": "pwlink",
            "requires_consent": False,
            "password": "letmein123",
        },
    )
    assert create_resp.json()["is_password_protected"] is True
    await client.post("/api/v1/auth/logout")

    meta_resp = await client.get("/api/v1/t/pwlink/meta")
    assert meta_resp.json()["needs_password"] is True

    wrong_resp = await client.post("/api/v1/t/pwlink/resolve", json={"password": "wrong"})
    assert wrong_resp.status_code == 401

    right_resp = await client.post("/api/v1/t/pwlink/resolve", json={"password": "letmein123"})
    assert right_resp.status_code == 200
    assert right_resp.json()["target_url"] == "https://example.com/secret"


async def test_disabled_link_returns_not_found_reason(client):
    await _register_and_login(client)
    create_resp = await client.post(
        "/api/v1/links",
        json={"target_url": "https://example.com", "custom_alias": "disabledlink", "requires_consent": False},
    )
    link_id = create_resp.json()["id"]
    patch_resp = await client.patch(f"/api/v1/links/{link_id}", json={"is_active": False})
    assert patch_resp.status_code == 200

    redirect_resp = await client.get("/t/disabledlink", follow_redirects=False)
    assert "DISABLED" in redirect_resp.headers["location"]


async def test_set_link_password_can_remove_protection(client):
    await _register_and_login(client)
    create_resp = await client.post(
        "/api/v1/links",
        json={
            "target_url": "https://example.com",
            "custom_alias": "removepw",
            "password": "initialpass",
        },
    )
    link_id = create_resp.json()["id"]

    remove_resp = await client.put(f"/api/v1/links/{link_id}/password", json={"password": None})
    assert remove_resp.status_code == 200
    assert remove_resp.json()["is_password_protected"] is False
