import asyncio
import uuid
from datetime import timedelta

import pytest

from app.core.config import get_settings
from app.core.security import create_jwt
from app.services import device_service, device_signaling_service
from app.services.exceptions import InvalidOrExpiredTokenError


@pytest.fixture(autouse=True)
def _enable_device_control():
    """
    The module defaults off (ENABLE_DEVICE_CONTROL=false) — flip it on for
    this test module regardless of the running .env, so these tests are
    self-contained rather than depending on local environment config.
    """
    settings = get_settings()
    original = settings.enable_device_control
    settings.enable_device_control = True
    yield
    settings.enable_device_control = original


async def _redis_reachable() -> bool:
    try:
        client = device_signaling_service._get_redis()
        await asyncio.wait_for(client.ping(), timeout=1.0)
        return True
    except Exception:
        return False


async def _register(client, email="owner@example.com", password="StrongPass123"):
    resp = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password, "full_name": "Owner"}
    )
    assert resp.status_code == 201
    return resp.json()


async def _pair_device(client, *, device_name="Test Phone"):
    pairing_resp = await client.post("/api/v1/devices/pairing-codes")
    assert pairing_resp.status_code == 201
    pairing = pairing_resp.json()

    exchange_resp = await client.post(
        f"/api/v1/devices/pairing-codes/{pairing['code']}/exchange",
        json={
            "code": pairing["code"],
            "device_name": device_name,
            "device_fingerprint": "fingerprint-abc",
            "platform": "android",
        },
    )
    assert exchange_resp.status_code == 200
    return exchange_resp.json()


# --- Feature flag --------------------------------------------------------------


async def test_devices_module_404_when_disabled(client):
    settings = get_settings()
    settings.enable_device_control = False
    try:
        await _register(client)
        resp = await client.get("/api/v1/devices")
        assert resp.status_code == 404
    finally:
        settings.enable_device_control = True


# --- Pairing ---------------------------------------------------------------------


async def test_pairing_round_trip_and_device_list(client):
    await _register(client)

    paired = await _pair_device(client)
    assert paired["device"]["name"] == "Test Phone"
    assert paired["device"]["is_active"] is True
    assert paired["device_secret"]

    list_resp = await client.get("/api/v1/devices")
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == paired["device"]["id"]
    # The device secret is never re-exposed by the list endpoint.
    assert "device_secret" not in body["items"][0]


async def test_pairing_exchange_rejects_bad_code(client):
    await _register(client)
    await client.post("/api/v1/devices/pairing-codes")  # generates a real code, but we don't use it

    resp = await client.post(
        "/api/v1/devices/pairing-codes/WRONGCODE/exchange",
        json={
            "code": "WRONGCODE",
            "device_name": "Attacker Phone",
            "device_fingerprint": "x",
            "platform": "android",
        },
    )
    assert resp.status_code == 400


async def test_pairing_exchange_code_is_single_use(client):
    await _register(client)
    pairing = (await client.post("/api/v1/devices/pairing-codes")).json()

    body = {
        "code": pairing["code"],
        "device_name": "Phone",
        "device_fingerprint": "fp",
        "platform": "android",
    }
    first = await client.post(f"/api/v1/devices/pairing-codes/{pairing['code']}/exchange", json=body)
    assert first.status_code == 200

    second = await client.post(f"/api/v1/devices/pairing-codes/{pairing['code']}/exchange", json=body)
    assert second.status_code == 400


async def test_pairing_code_generation_is_rate_limited(client):
    await _register(client)
    statuses = []
    for _ in range(6):
        resp = await client.post("/api/v1/devices/pairing-codes")
        statuses.append(resp.status_code)
    assert statuses[:5] == [201] * 5
    assert statuses[5] == 429


async def test_pairing_exchange_is_rate_limited(client):
    await _register(client)
    body = {"code": "NOPE0000", "device_name": "x", "device_fingerprint": "x", "platform": "android"}
    statuses = []
    for _ in range(11):
        resp = await client.post("/api/v1/devices/pairing-codes/NOPE0000/exchange", json=body)
        statuses.append(resp.status_code)
    assert statuses[:10] == [400] * 10  # wrong code, but allowed through
    assert statuses[10] == 429


# --- Ownership / IDOR ------------------------------------------------------------


async def test_device_idor_protection(client):
    await _register(client, email="owner@example.com")
    paired = await _pair_device(client)
    device_id = paired["device"]["id"]
    await client.post("/api/v1/auth/logout")

    await _register(client, email="attacker@example.com")

    rename_resp = await client.patch(f"/api/v1/devices/{device_id}", json={"name": "Hijacked"})
    assert rename_resp.status_code == 404

    revoke_resp = await client.post(f"/api/v1/devices/{device_id}/revoke")
    assert revoke_resp.status_code == 404

    sessions_resp = await client.get(f"/api/v1/devices/{device_id}/sessions")
    assert sessions_resp.status_code == 404

    start_resp = await client.post(f"/api/v1/devices/{device_id}/sessions")
    assert start_resp.status_code == 404


async def test_device_rename_and_revoke(client):
    await _register(client)
    paired = await _pair_device(client)
    device_id = paired["device"]["id"]

    rename_resp = await client.patch(f"/api/v1/devices/{device_id}", json={"name": "Renamed Phone"})
    assert rename_resp.status_code == 200
    assert rename_resp.json()["name"] == "Renamed Phone"

    revoke_resp = await client.post(f"/api/v1/devices/{device_id}/revoke")
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["is_active"] is False

    # A revoked device can no longer start a new session.
    start_resp = await client.post(f"/api/v1/devices/{device_id}/sessions")
    assert start_resp.status_code == 404


# --- Sessions + device-secret auth ------------------------------------------------


async def test_session_start_and_device_token_issuance(client):
    await _register(client)
    paired = await _pair_device(client)
    device_id = paired["device"]["id"]
    device_secret = paired["device_secret"]

    start_resp = await client.post(f"/api/v1/devices/{device_id}/sessions")
    assert start_resp.status_code == 201
    session = start_resp.json()
    assert session["web_ticket"]
    assert any(s["urls"].startswith("stun:") for s in session["ice_servers"])

    token_resp = await client.post(
        f"/api/v1/devices/{device_id}/sessions/token",
        json={"session_id": session["session_id"]},
        headers={"Authorization": f"Bearer {device_secret}"},
    )
    assert token_resp.status_code == 200
    assert token_resp.json()["ticket"]


async def test_session_token_rejects_wrong_device_secret(client):
    await _register(client)
    paired = await _pair_device(client)
    device_id = paired["device"]["id"]

    start_resp = await client.post(f"/api/v1/devices/{device_id}/sessions")
    session = start_resp.json()

    token_resp = await client.post(
        f"/api/v1/devices/{device_id}/sessions/token",
        json={"session_id": session["session_id"]},
        headers={"Authorization": "Bearer not-the-real-secret"},
    )
    assert token_resp.status_code == 401


async def test_pending_session_reports_null_then_session_id(client):
    await _register(client)
    paired = await _pair_device(client)
    device_id = paired["device"]["id"]
    device_secret = paired["device_secret"]
    auth = {"Authorization": f"Bearer {device_secret}"}

    before_resp = await client.get(f"/api/v1/devices/{device_id}/sessions/pending", headers=auth)
    assert before_resp.status_code == 200
    assert before_resp.json()["session_id"] is None

    session = (await client.post(f"/api/v1/devices/{device_id}/sessions")).json()

    after_resp = await client.get(f"/api/v1/devices/{device_id}/sessions/pending", headers=auth)
    assert after_resp.status_code == 200
    assert after_resp.json()["session_id"] == session["session_id"]


async def test_pending_session_rejects_wrong_or_missing_device_secret(client):
    await _register(client)
    paired = await _pair_device(client)
    device_id = paired["device"]["id"]

    wrong_secret_resp = await client.get(
        f"/api/v1/devices/{device_id}/sessions/pending",
        headers={"Authorization": "Bearer not-the-real-secret"},
    )
    assert wrong_secret_resp.status_code == 401

    missing_resp = await client.get(f"/api/v1/devices/{device_id}/sessions/pending")
    assert missing_resp.status_code == 401


async def test_session_end(client):
    await _register(client)
    paired = await _pair_device(client)
    device_id = paired["device"]["id"]
    session = (await client.post(f"/api/v1/devices/{device_id}/sessions")).json()

    end_resp = await client.post(f"/api/v1/devices/{device_id}/sessions/{session['session_id']}/end")
    assert end_resp.status_code == 200
    assert end_resp.json()["status"] == "ENDED"


# --- WS ticket validation (unit-level, no live socket needed) --------------------


async def test_validate_ws_ticket_accepts_matching_session_and_role():
    session_id = uuid.uuid4()
    ticket = create_jwt(
        subject="user-1",
        token_type="device_ws",
        expires_delta=timedelta(seconds=30),
        extra_claims={"session_id": str(session_id), "role": "controller"},
    )
    claims = await device_service.validate_ws_ticket(ticket, expected_session_id=session_id)
    assert claims["role"] == "controller"


async def test_validate_ws_ticket_rejects_wrong_session():
    ticket = create_jwt(
        subject="user-1",
        token_type="device_ws",
        expires_delta=timedelta(seconds=30),
        extra_claims={"session_id": str(uuid.uuid4()), "role": "controller"},
    )
    with pytest.raises(InvalidOrExpiredTokenError):
        await device_service.validate_ws_ticket(ticket, expected_session_id=uuid.uuid4())


async def test_validate_ws_ticket_rejects_expired_token():
    session_id = uuid.uuid4()
    ticket = create_jwt(
        subject="user-1",
        token_type="device_ws",
        expires_delta=timedelta(seconds=-1),
        extra_claims={"session_id": str(session_id), "role": "controller"},
    )
    with pytest.raises(InvalidOrExpiredTokenError):
        await device_service.validate_ws_ticket(ticket, expected_session_id=session_id)


async def test_validate_ws_ticket_rejects_wrong_token_type():
    session_id = uuid.uuid4()
    ticket = create_jwt(
        subject="user-1",
        token_type="access",
        expires_delta=timedelta(seconds=30),
        extra_claims={"session_id": str(session_id), "role": "controller"},
    )
    with pytest.raises(InvalidOrExpiredTokenError):
        await device_service.validate_ws_ticket(ticket, expected_session_id=session_id)


# --- Signaling relay (Redis pub/sub round trip) -----------------------------------


async def test_signal_relay_round_trip_without_self_echo():
    if not await _redis_reachable():
        pytest.skip("Redis not reachable from this test environment")

    session_id = uuid.uuid4()

    async with device_signaling_service.SignalRelay(session_id, "controller") as controller_relay:
        async with device_signaling_service.SignalRelay(session_id, "target") as target_relay:
            await device_signaling_service.publish_signal(session_id, "controller", {"type": "offer", "data": {"sdp": "x"}})

            target_iter = target_relay.listen()
            received = await asyncio.wait_for(target_iter.__anext__(), timeout=5.0)
            assert received == {"type": "offer", "data": {"sdp": "x"}}

            # The controller's own relay must NOT receive its own message
            # (each role listens on a distinct channel — see
            # device_signaling_service.py's _OTHER_ROLE routing).
            await device_signaling_service.publish_signal(session_id, "target", {"type": "answer", "data": {"sdp": "y"}})
            controller_iter = controller_relay.listen()
            received_answer = await asyncio.wait_for(controller_iter.__anext__(), timeout=5.0)
            assert received_answer == {"type": "answer", "data": {"sdp": "y"}}
