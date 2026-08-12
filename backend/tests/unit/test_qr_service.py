import pytest

from app.services.exceptions import ServiceError
from app.services.qr_service import (
    InvalidQrParamsError,
    generate_qr_png,
    generate_qr_svg,
    logo_path_for,
)


def test_generate_qr_png_returns_valid_png_bytes():
    data = generate_qr_png("https://example.com", size=128)
    assert data[:8] == b"\x89PNG\r\n\x1a\n"


def test_generate_qr_svg_returns_svg_markup():
    data = generate_qr_svg("https://example.com")
    assert data.strip().startswith(b"<?xml") or b"<svg" in data


@pytest.mark.parametrize("size", [10, 5000])
def test_generate_qr_png_rejects_out_of_range_size(size):
    with pytest.raises(InvalidQrParamsError):
        generate_qr_png("https://example.com", size=size)


@pytest.mark.parametrize("color", ["notacolor", "#12", "#1234567"])
def test_generate_qr_png_rejects_invalid_colors(color):
    with pytest.raises(InvalidQrParamsError):
        generate_qr_png("https://example.com", fg_color=color)


def test_generate_qr_png_rejects_invalid_error_correction():
    with pytest.raises(InvalidQrParamsError):
        generate_qr_png("https://example.com", error_correction="Z")


def test_generate_qr_png_and_svg_errors_are_service_errors():
    assert issubclass(InvalidQrParamsError, ServiceError)


@pytest.mark.parametrize(
    "logo_id",
    [
        "../../etc/passwd",
        "..%2f..%2fetc%2fpasswd",
        "not-a-real-uuid.png",
        "a" * 32 + ".exe",
    ],
)
def test_logo_path_for_rejects_anything_not_a_generated_filename(logo_id):
    assert logo_path_for(logo_id) is None
