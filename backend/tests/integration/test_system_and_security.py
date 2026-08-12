async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_ready_check_reports_component_status(client):
    resp = await client.get("/ready")
    assert resp.status_code in (200, 503)
    body = resp.json()
    assert "components" in body
    assert set(body["components"].keys()) == {"database", "redis"}


async def test_security_headers_present_on_every_response(client):
    resp = await client.get("/health")
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert resp.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "permissions-policy" in resp.headers
    assert "content-security-policy" in resp.headers


async def test_cors_preflight_allows_configured_frontend_origin(client):
    resp = await client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert resp.status_code in (200, 204)
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"


async def test_unknown_route_returns_standard_error_envelope(client):
    resp = await client.get("/api/v1/this-route-does-not-exist")
    assert resp.status_code == 404
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == 404
    assert "message" in body["error"]


async def test_validation_error_returns_standard_envelope_with_details(client):
    resp = await client.post("/api/v1/auth/register", json={"password": "short"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == 422
    assert isinstance(body["error"]["details"], list)
    assert len(body["error"]["details"]) > 0


async def test_uploads_are_served_as_static_files(client):
    resp = await client.get("/uploads/avatars/does-not-exist.png")
    assert resp.status_code == 404
