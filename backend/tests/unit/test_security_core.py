
from app.core.security import (
    create_access_token,
    decode_jwt,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.enums import ROLE_HIERARCHY, UserRole


def test_password_hash_roundtrip():
    hashed = hash_password("Sup3r$ecretPass!")
    assert hashed != "Sup3r$ecretPass!"
    assert verify_password("Sup3r$ecretPass!", hashed)
    assert not verify_password("wrong-password", hashed)


def test_hash_token_is_deterministic_and_one_way():
    token = "some-opaque-token"
    h1 = hash_token(token)
    h2 = hash_token(token)
    assert h1 == h2
    assert h1 != token


def test_access_token_roundtrip():
    token = create_access_token(user_id="11111111-1111-1111-1111-111111111111", role="USER")
    payload = decode_jwt(token)
    assert payload is not None
    assert payload["sub"] == "11111111-1111-1111-1111-111111111111"
    assert payload["type"] == "access"
    assert payload["role"] == "USER"


def test_tampered_jwt_is_rejected():
    token = create_access_token(user_id="11111111-1111-1111-1111-111111111111", role="USER")
    tampered = token[:-2] + ("aa" if token[-2:] != "aa" else "bb")
    assert decode_jwt(tampered) is None


def test_role_hierarchy_ordering():
    assert ROLE_HIERARCHY.index(UserRole.VIEWER) < ROLE_HIERARCHY.index(UserRole.USER)
    assert ROLE_HIERARCHY.index(UserRole.USER) < ROLE_HIERARCHY.index(UserRole.MANAGER)
    assert ROLE_HIERARCHY.index(UserRole.MANAGER) < ROLE_HIERARCHY.index(UserRole.ADMIN)
    assert ROLE_HIERARCHY.index(UserRole.ADMIN) < ROLE_HIERARCHY.index(UserRole.SUPER_ADMIN)
