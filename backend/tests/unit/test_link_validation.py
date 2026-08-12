import pytest

from app.utils.short_code import generate_short_code, is_reserved, is_valid_alias_format
from app.utils.url_validation import validate_target_url


def test_generate_short_code_length_and_charset():
    code = generate_short_code()
    assert len(code) == 7
    assert code.isalnum()


def test_generate_short_code_is_random():
    codes = {generate_short_code() for _ in range(50)}
    assert len(codes) == 50  # astronomically unlikely to collide


@pytest.mark.parametrize("alias", ["abc", "summer-2026", "my_link_1", "a" * 64])
def test_valid_alias_formats(alias):
    assert is_valid_alias_format(alias)


@pytest.mark.parametrize("alias", ["ab", "has space", "slash/es", "a" * 65, "emoji😀"])
def test_invalid_alias_formats(alias):
    assert not is_valid_alias_format(alias)


def test_reserved_words_blocked_case_insensitive():
    assert is_reserved("admin")
    assert is_reserved("ADMIN")
    assert is_reserved("Api")
    assert not is_reserved("my-custom-alias")


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "http://example.com/path?query=1",
        "https://sub.example.com:8443/a/b",
    ],
)
def test_valid_target_urls(url):
    assert validate_target_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "ftp://example.com/file",
        "http://localhost/admin",
        "http://127.0.0.1/",
        "http://169.254.169.254/latest/meta-data",
        "http://10.0.0.5/internal",
        "not-a-url",
        "",
    ],
)
def test_invalid_target_urls_rejected(url):
    with pytest.raises(ValueError):
        validate_target_url(url)
