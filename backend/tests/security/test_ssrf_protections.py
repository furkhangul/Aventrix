"""
SSRF coverage for the new server-side-fetching modules (URL Tools, Security
Center, Webhooks). app/utils/safe_fetch.py's own validation logic is unit
tested directly in tests/unit/test_safe_fetch.py; these tests confirm it is
actually wired into every endpoint that accepts an attacker-controlled URL.
"""

PRIVATE_TARGETS = [
    "http://127.0.0.1:8000/admin",
    "http://localhost/",
    "http://169.254.169.254/latest/meta-data",
    "http://192.168.1.1/",
]


async def _register(client, email="owner@example.com"):
    resp = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "StrongPass123", "full_name": "Owner"}
    )
    assert resp.status_code == 201


async def test_url_tools_analyze_rejects_private_targets(client):
    await _register(client)
    for target in PRIVATE_TARGETS:
        resp = await client.post("/api/v1/url-tools/analyze", json={"url": target})
        assert resp.status_code == 422, target


async def test_url_tools_redirect_check_rejects_private_targets(client):
    await _register(client)
    for target in PRIVATE_TARGETS:
        resp = await client.post("/api/v1/url-tools/redirect-check", json={"url": target})
        assert resp.status_code == 422, target


async def test_security_center_scan_rejects_private_domains(client):
    await _register(client)
    for domain in ["localhost", "127.0.0.1", "169.254.169.254"]:
        resp = await client.post("/api/v1/security-center/scan", json={"domain": domain})
        assert resp.status_code == 422, domain


async def test_webhook_create_rejects_private_and_metadata_targets(client):
    await _register(client)
    for target in PRIVATE_TARGETS:
        resp = await client.post("/api/v1/webhooks", json={"url": target, "events": ["link.created"]})
        assert resp.status_code == 422, target
