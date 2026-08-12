import pytest

from app.utils.safe_fetch import UnsafeUrlError, validate_url_for_fetch


async def test_validate_url_for_fetch_accepts_a_public_url():
    result = await validate_url_for_fetch("https://example.com")
    assert result == "https://example.com"


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com",
        "javascript:alert(1)",
        "https://",
        "http://localhost/",
        "http://localhost:8000/admin",
        "http://0.0.0.0/",
        "http://127.0.0.1/",
        "http://127.0.0.1:5432/",
        "http://192.168.1.1/",
        "http://10.0.0.5/",
        "http://172.16.0.1/",
        "http://169.254.1.1/",  # link-local
        "http://169.254.169.254/latest/meta-data",  # cloud metadata
        "http://[::1]/",  # IPv6 loopback
        "http://this-domain-should-not-exist-9f2c8a41.invalid/",  # unresolvable
        "https://example.com/" + "a" * 3000,  # too long
    ],
)
async def test_validate_url_for_fetch_rejects_unsafe_targets(url):
    with pytest.raises(UnsafeUrlError):
        await validate_url_for_fetch(url)
