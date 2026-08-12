async def _register(client, email="owner@example.com", password="StrongPass123"):
    resp = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password, "full_name": "Owner"}
    )
    assert resp.status_code == 201
    return resp.json()


async def _create_link(client, target_url="https://example.com/landing"):
    resp = await client.post("/api/v1/links", json={"target_url": target_url, "requires_consent": False})
    assert resp.status_code == 201
    return resp.json()


# --- Analytics ---------------------------------------------------------------


async def test_analytics_overview_and_export(client):
    await _register(client)
    link = await _create_link(client)

    resp = await client.get("/api/v1/analytics/overview")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_visits"] == 0

    scoped = await client.get(f"/api/v1/analytics/overview?link_id={link['id']}")
    assert scoped.status_code == 200

    export_csv = await client.get("/api/v1/analytics/export?format=csv")
    assert export_csv.status_code == 200
    assert "text/csv" in export_csv.headers["content-type"]

    export_json = await client.get("/api/v1/analytics/export?format=json")
    assert export_json.status_code == 200
    assert "application/json" in export_json.headers["content-type"]


async def test_analytics_rejects_unowned_link_filter(client):
    await _register(client, email="owner@example.com")
    link = await _create_link(client)
    await client.post("/api/v1/auth/logout")

    await _register(client, email="attacker@example.com")
    resp = await client.get(f"/api/v1/analytics/overview?link_id={link['id']}")
    assert resp.status_code == 404


# --- QR Codes ------------------------------------------------------------------


async def test_qr_generate_png_and_svg(client):
    await _register(client)
    link = await _create_link(client)

    png_resp = await client.get("/api/v1/qr/generate?data=https://example.com")
    assert png_resp.status_code == 200
    assert png_resp.headers["content-type"] == "image/png"
    assert png_resp.content[:8] == b"\x89PNG\r\n\x1a\n"

    svg_resp = await client.get("/api/v1/qr/generate?data=https://example.com&format=svg")
    assert svg_resp.status_code == 200
    assert svg_resp.headers["content-type"] == "image/svg+xml"

    link_qr = await client.get(f"/api/v1/qr/links/{link['id']}")
    assert link_qr.status_code == 200


async def test_qr_generate_rejects_bad_params(client):
    await _register(client)
    resp = await client.get("/api/v1/qr/generate?data=https://example.com&size=1")
    assert resp.status_code == 422

    resp2 = await client.get("/api/v1/qr/generate?data=https://example.com&fg_color=notacolor")
    assert resp2.status_code == 422


# --- API keys --------------------------------------------------------------


async def test_api_key_create_rotate_revoke_and_authenticate(client):
    await _register(client)

    create_resp = await client.post("/api/v1/api-keys", json={"name": "CI key", "tier": "FREE"})
    assert create_resp.status_code == 201
    created = create_resp.json()
    raw_key = created["api_key"]
    assert raw_key.startswith("fw_live_")

    # The raw key authenticates like a bearer token, independent of the session cookie.
    auth_resp = await client.get("/api/v1/links", headers={"Authorization": f"Bearer {raw_key}"})
    assert auth_resp.status_code == 200

    list_resp = await client.get("/api/v1/api-keys")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    rotate_resp = await client.post(f"/api/v1/api-keys/{created['id']}/rotate")
    assert rotate_resp.status_code == 200
    rotated = rotate_resp.json()
    assert rotated["api_key"] != raw_key

    # The old key no longer works after rotation.
    old_key_resp = await client.get("/api/v1/links", headers={"Authorization": f"Bearer {raw_key}"})
    assert old_key_resp.status_code == 401

    revoke_resp = await client.delete(f"/api/v1/api-keys/{rotated['id']}")
    assert revoke_resp.status_code == 204

    revoked_key_resp = await client.get("/api/v1/links", headers={"Authorization": f"Bearer {rotated['api_key']}"})
    assert revoked_key_resp.status_code == 401


async def test_api_key_idor_protection(client):
    await _register(client, email="owner@example.com")
    created = (await client.post("/api/v1/api-keys", json={"name": "k", "tier": "FREE"})).json()
    await client.post("/api/v1/auth/logout")

    await _register(client, email="attacker@example.com")
    resp = await client.delete(f"/api/v1/api-keys/{created['id']}")
    assert resp.status_code == 404


# --- Webhooks ----------------------------------------------------------------


async def test_webhook_create_list_and_test_delivery(client):
    await _register(client)

    create_resp = await client.post(
        "/api/v1/webhooks",
        json={"url": "https://example.com/hooks/inbound", "events": ["link.created", "link.clicked"]},
    )
    assert create_resp.status_code == 201
    webhook = create_resp.json()
    assert webhook["secret"].startswith("whsec_")
    assert webhook["secret_preview"].endswith("…")

    list_resp = await client.get("/api/v1/webhooks")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1
    # The list endpoint never re-exposes the full secret.
    assert "secret" not in list_resp.json()["items"][0]

    test_resp = await client.post(f"/api/v1/webhooks/{webhook['id']}/test")
    assert test_resp.status_code == 200
    assert test_resp.json()["event_type"] == "webhook.test"

    deliveries_resp = await client.get(f"/api/v1/webhooks/{webhook['id']}/deliveries")
    assert deliveries_resp.status_code == 200
    assert deliveries_resp.json()["total"] == 1


async def test_webhook_create_rejects_private_target(client):
    await _register(client)
    resp = await client.post(
        "/api/v1/webhooks", json={"url": "http://localhost:8000/hook", "events": ["link.created"]}
    )
    assert resp.status_code == 422


async def test_webhook_idor_protection(client):
    await _register(client, email="owner@example.com")
    webhook = (
        await client.post(
            "/api/v1/webhooks", json={"url": "https://example.com/hook", "events": ["link.created"]}
        )
    ).json()
    await client.post("/api/v1/auth/logout")

    await _register(client, email="attacker@example.com")
    resp = await client.delete(f"/api/v1/webhooks/{webhook['id']}")
    assert resp.status_code == 404


# --- Notifications -----------------------------------------------------------


async def test_notification_first_visit_and_list(client):
    await _register(client)
    link = await _create_link(client)

    resolve_resp = await client.get(f"/t/{link['short_code']}", follow_redirects=False)
    assert resolve_resp.status_code == 302

    list_resp = await client.get("/api/v1/notifications")
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["unread_count"] >= 1
    assert any(n["type"] == "LINK_FIRST_VISIT" for n in body["items"])

    notification_id = body["items"][0]["id"]
    read_resp = await client.patch(f"/api/v1/notifications/{notification_id}/read")
    assert read_resp.status_code == 200
    assert read_resp.json()["is_read"] is True


async def test_notification_preferences_roundtrip(client):
    await _register(client)
    resp = await client.patch("/api/v1/notifications/preferences", json={"preferences": {"LINK_EXPIRED": False}})
    assert resp.status_code == 200
    assert resp.json()["preferences"]["LINK_EXPIRED"] is False

    get_resp = await client.get("/api/v1/notifications/preferences")
    assert get_resp.status_code == 200
    assert get_resp.json()["preferences"]["LINK_EXPIRED"] is False
