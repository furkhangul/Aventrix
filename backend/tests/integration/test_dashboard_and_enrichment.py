from sqlalchemy import select

from app.models.visit import Visit
from app.services.ip_intelligence_service import enrich_visit


async def _register_and_login(client, email="owner@example.com", password="StrongPass123"):
    resp = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password, "full_name": "Owner"}
    )
    assert resp.status_code == 201
    return resp.json()


async def test_dashboard_summary_reflects_recorded_visits(client):
    await _register_and_login(client)
    campaign_resp = await client.post("/api/v1/campaigns", json={"name": "Launch"})
    campaign_id = campaign_resp.json()["id"]

    link_resp = await client.post(
        "/api/v1/links",
        json={
            "target_url": "https://example.com/landing",
            "campaign_id": campaign_id,
            "custom_alias": "dashlink",
            "requires_consent": False,
        },
    )
    assert link_resp.status_code == 201

    for i in range(3):
        r = await client.get(
            "/t/dashlink", follow_redirects=False, headers={"X-Forwarded-For": f"203.0.113.{i}"}
        )
        assert r.status_code == 302

    summary_resp = await client.get("/api/v1/dashboard/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["total_links"] == 1
    assert summary["total_visits"] == 3
    assert summary["unique_visitors"] == 3
    assert summary["today_visits"] == 3
    assert summary["active_campaigns"] == 1
    assert summary["conversion_rate"] == 100.0


async def test_dashboard_timeseries_includes_today_bucket(client):
    await _register_and_login(client)
    await client.post(
        "/api/v1/links",
        json={"target_url": "https://example.com", "custom_alias": "tslink", "requires_consent": False},
    )
    await client.get("/t/tslink", follow_redirects=False)

    resp = await client.get("/api/v1/dashboard/timeseries?range=7d")
    assert resp.status_code == 200
    points = resp.json()
    assert sum(p["count"] for p in points) == 1
    assert len(points) == 7


async def test_dashboard_scoped_to_owner_only(client):
    await _register_and_login(client, email="a@example.com")
    await client.post(
        "/api/v1/links",
        json={"target_url": "https://example.com", "custom_alias": "ownerlink-a", "requires_consent": False},
    )
    await client.get("/t/ownerlink-a", follow_redirects=False)
    await client.post("/api/v1/auth/logout")

    await _register_and_login(client, email="b@example.com")
    resp = await client.get("/api/v1/dashboard/summary")
    body = resp.json()
    assert body["total_links"] == 0
    assert body["total_visits"] == 0


async def test_enrich_visit_populates_ip_intelligence_fields(client, db_session):
    await _register_and_login(client)
    await client.post(
        "/api/v1/links",
        json={"target_url": "https://example.com", "custom_alias": "enrichlink", "requires_consent": False},
    )
    await client.get("/t/enrichlink", follow_redirects=False, headers={"X-Forwarded-For": "203.0.113.42"})

    result = await db_session.execute(select(Visit).where(Visit.consent_given.is_(True)))
    visit = result.scalars().first()
    assert visit is not None
    assert visit.country is None  # not yet enriched — worker hasn't run in this test

    await enrich_visit(db_session, visit.id, "203.0.113.42")

    await db_session.refresh(visit)
    assert visit.country is not None
    assert visit.isp is not None
    # A real provider (ip-api) may not disambiguate VPN specifically from
    # proxy/Tor and reports UNKNOWN in that case; the mock provider always
    # commits to YES/NO. Both are valid depending on IP_PROVIDER/.env.
    assert visit.is_vpn in {"YES", "NO", "UNKNOWN"}


async def test_enrich_visit_is_noop_when_consent_withheld(client, db_session):
    await _register_and_login(client)
    await client.post(
        "/api/v1/links",
        json={"target_url": "https://example.com", "custom_alias": "noconsentlink", "requires_consent": True},
    )
    await client.post("/api/v1/auth/logout")
    await client.post("/api/v1/t/noconsentlink/resolve", json={"consent": False})

    result = await db_session.execute(select(Visit))
    visit = result.scalars().first()
    assert visit.consent_given is False

    await enrich_visit(db_session, visit.id, "203.0.113.99")
    await db_session.refresh(visit)
    assert visit.country is None


async def test_top_dimension_reflects_enriched_visits(client, db_session):
    await _register_and_login(client)
    await client.post(
        "/api/v1/links",
        json={"target_url": "https://example.com", "custom_alias": "topdim", "requires_consent": False},
    )
    await client.get("/t/topdim", follow_redirects=False, headers={"X-Forwarded-For": "198.51.100.7"})

    result = await db_session.execute(select(Visit))
    visit = result.scalars().first()
    await enrich_visit(db_session, visit.id, "198.51.100.7")

    resp = await client.get("/api/v1/dashboard/top/country")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["count"] == 1


async def test_top_dimension_rejects_unknown_dimension(client):
    await _register_and_login(client)
    resp = await client.get("/api/v1/dashboard/top/not-a-real-dimension")
    assert resp.status_code == 400
