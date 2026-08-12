import pyotp
import pytest

from app.integrations.email.mock_provider import MockEmailProvider


@pytest.fixture(autouse=True)
def _clear_outbox():
    MockEmailProvider.clear_outbox()
    yield
    MockEmailProvider.clear_outbox()


async def _register(client, email="alice@example.com", password="StrongPass123"):
    return await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Alice Example"},
    )


async def test_register_sets_cookies_and_creates_user(client):
    resp = await _register(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert body["is_email_verified"] is False
    assert "access_token" in resp.cookies
    assert "refresh_token" in resp.cookies


async def test_register_duplicate_email_rejected(client):
    await _register(client)
    resp = await _register(client)
    assert resp.status_code == 409


async def test_register_weak_password_rejected(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "bob@example.com", "password": "weak", "full_name": "Bob"},
    )
    assert resp.status_code == 422


async def test_login_success_and_me(client):
    await _register(client)
    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "alice@example.com", "password": "StrongPass123"}
    )
    assert login_resp.status_code == 200
    assert login_resp.json()["user"]["email"] == "alice@example.com"

    me_resp = await client.get("/api/v1/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "alice@example.com"


async def test_login_wrong_password_fails(client):
    await _register(client)
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "alice@example.com", "password": "WrongPassword1"}
    )
    assert resp.status_code == 401


async def test_login_rate_limited_after_five_attempts(client):
    await _register(client)
    for _ in range(5):
        resp = await client.post(
            "/api/v1/auth/login", json={"email": "alice@example.com", "password": "WrongPassword1"}
        )
        assert resp.status_code == 401
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "alice@example.com", "password": "WrongPassword1"}
    )
    assert resp.status_code == 429


async def test_logout_clears_session(client):
    await _register(client)
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 200
    me_resp = await client.get("/api/v1/auth/me")
    assert me_resp.status_code == 401


async def test_refresh_rotates_tokens(client):
    await _register(client)
    old_refresh = client.cookies.get("refresh_token")
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 200
    new_refresh = client.cookies.get("refresh_token")
    assert new_refresh != old_refresh

    me_resp = await client.get("/api/v1/auth/me")
    assert me_resp.status_code == 200


async def test_email_verification_flow(client):
    await _register(client)
    sent = MockEmailProvider.get_outbox()
    assert len(sent) == 1
    token = sent[0].body_text.split("token=")[1].strip()

    resp = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert resp.status_code == 200

    me_resp = await client.get("/api/v1/auth/me")
    assert me_resp.json()["is_email_verified"] is True


async def test_verify_email_invalid_token_rejected(client):
    resp = await client.post("/api/v1/auth/verify-email", json={"token": "not-a-real-token"})
    assert resp.status_code == 400


async def test_forgot_and_reset_password(client):
    await _register(client)
    await client.post("/api/v1/auth/logout")

    MockEmailProvider.clear_outbox()
    resp = await client.post("/api/v1/auth/forgot-password", json={"email": "alice@example.com"})
    assert resp.status_code == 200
    sent = MockEmailProvider.get_outbox()
    assert len(sent) == 1
    token = sent[0].body_text.split("token=")[1].split()[0]

    reset_resp = await client.post(
        "/api/v1/auth/reset-password", json={"token": token, "new_password": "NewStrongPass123"}
    )
    assert reset_resp.status_code == 200

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "alice@example.com", "password": "NewStrongPass123"}
    )
    assert login_resp.status_code == 200


async def test_forgot_password_unknown_email_does_not_leak(client):
    resp = await client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})
    assert resp.status_code == 200


async def test_change_password_requires_current_password(client):
    await _register(client)
    resp = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "WrongOne123", "new_password": "AnotherStrong123"},
    )
    assert resp.status_code == 401


async def test_change_password_success(client):
    await _register(client)
    resp = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "StrongPass123", "new_password": "AnotherStrong123"},
    )
    assert resp.status_code == 200


async def test_profile_update(client):
    await _register(client)
    resp = await client.patch("/api/v1/auth/me", json={"full_name": "Alice Updated"})
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Alice Updated"


async def test_sessions_list_and_revoke(client):
    await _register(client)
    resp = await client.get("/api/v1/auth/sessions")
    assert resp.status_code == 200
    sessions = resp.json()
    assert len(sessions) == 1
    assert sessions[0]["is_current"] is True

    other_session_id = sessions[0]["id"]
    revoke_resp = await client.delete(f"/api/v1/auth/sessions/{other_session_id}")
    assert revoke_resp.status_code == 200


async def test_login_history_records_attempts(client):
    await _register(client)
    await client.post("/api/v1/auth/login", json={"email": "alice@example.com", "password": "wrong-pass-1"})
    resp = await client.get("/api/v1/auth/login-history")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 2  # register-time login + the failed attempt


async def test_two_factor_full_lifecycle(client):
    await _register(client)

    setup_resp = await client.post("/api/v1/auth/2fa/setup")
    assert setup_resp.status_code == 200
    secret = setup_resp.json()["secret"]

    code = pyotp.TOTP(secret).now()
    confirm_resp = await client.post("/api/v1/auth/2fa/confirm", json={"code": code})
    assert confirm_resp.status_code == 200

    await client.post("/api/v1/auth/logout")

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "alice@example.com", "password": "StrongPass123"}
    )
    assert login_resp.status_code == 200
    assert login_resp.json()["requires_2fa"] is True
    pending_token = login_resp.json()["two_factor_pending_token"]

    me_resp = await client.get("/api/v1/auth/me")
    assert me_resp.status_code == 401  # not logged in yet, only 2FA-pending

    code2 = pyotp.TOTP(secret).now()
    verify_resp = await client.post(
        "/api/v1/auth/2fa/verify-login",
        json={"two_factor_pending_token": pending_token, "code": code2},
    )
    assert verify_resp.status_code == 200

    me_resp = await client.get("/api/v1/auth/me")
    assert me_resp.status_code == 200


async def test_account_deletion_requires_password(client):
    await _register(client)
    bad_resp = await client.request(
        "DELETE", "/api/v1/auth/me", json={"password": "WrongPassword1"}
    )
    assert bad_resp.status_code == 401

    good_resp = await client.request(
        "DELETE", "/api/v1/auth/me", json={"password": "StrongPass123"}
    )
    assert good_resp.status_code == 200

    me_resp = await client.get("/api/v1/auth/me")
    assert me_resp.status_code == 401
