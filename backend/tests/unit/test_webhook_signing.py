import hashlib
import hmac

from app.services.webhook_service import sign_payload


def test_sign_payload_matches_manual_hmac_sha256():
    secret = "whsec_test123"
    payload = '{"event":"link.created"}'

    signature = sign_payload(secret, payload)

    expected_digest = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    assert signature == f"sha256={expected_digest}"


def test_sign_payload_differs_for_different_secrets():
    payload = '{"event":"link.created"}'
    assert sign_payload("secret-a", payload) != sign_payload("secret-b", payload)


def test_sign_payload_differs_for_different_payloads():
    secret = "whsec_test123"
    assert sign_payload(secret, "a") != sign_payload(secret, "b")
