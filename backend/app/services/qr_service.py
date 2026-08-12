import io
import re
import uuid
from pathlib import Path

import qrcode
import qrcode.image.svg
from fastapi import UploadFile
from PIL import Image
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q

from app.services.exceptions import ServiceError
from app.services.profile_service import UPLOAD_ROOT

QR_LOGO_DIR = UPLOAD_ROOT / "qr-logos"
ALLOWED_LOGO_TYPES = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
MAX_LOGO_BYTES = 1 * 1024 * 1024  # 1MB

MIN_SIZE = 64
MAX_SIZE = 2000

ERROR_CORRECTION_LEVELS = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}

# Filenames are always ones we generated (uuid4 hex + a fixed extension) —
# never derived from user input beyond selecting one we already wrote. This
# pattern is the entire path-traversal defense for logo_path_for().
_LOGO_FILENAME_PATTERN = re.compile(r"^[0-9a-f]{32}\.(png|jpg|webp)$")


class UnsupportedLogoTypeError(ServiceError):
    pass


class LogoTooLargeError(ServiceError):
    pass


class InvalidQrParamsError(ServiceError):
    pass


def _validate_hex_color(value: str, field: str) -> str:
    stripped = value.lstrip("#")
    if len(stripped) not in (3, 6) or any(c not in "0123456789abcdefABCDEF" for c in stripped):
        raise InvalidQrParamsError(f"{field} must be a hex color like 'FFFFFF'")
    return f"#{stripped}"


def _validated_level(error_correction: str) -> int:
    level = ERROR_CORRECTION_LEVELS.get(error_correction.upper())
    if level is None:
        raise InvalidQrParamsError("error_correction must be one of L, M, Q, H")
    return level


def generate_qr_png(
    data: str,
    *,
    size: int = 300,
    fg_color: str = "000000",
    bg_color: str = "FFFFFF",
    error_correction: str = "M",
    logo_path: Path | None = None,
) -> bytes:
    if not (MIN_SIZE <= size <= MAX_SIZE):
        raise InvalidQrParamsError(f"size must be between {MIN_SIZE} and {MAX_SIZE} pixels")

    qr = qrcode.QRCode(error_correction=_validated_level(error_correction), border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(
        fill_color=_validate_hex_color(fg_color, "fg_color"),
        back_color=_validate_hex_color(bg_color, "bg_color"),
    ).convert("RGBA")
    img = img.resize((size, size), Image.LANCZOS)

    if logo_path is not None:
        logo = Image.open(logo_path).convert("RGBA")
        logo_size = size // 4
        logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
        # White backing square keeps the logo legible against QR modules.
        pad = max(4, logo_size // 8)
        backing = Image.new("RGBA", (logo_size + pad * 2, logo_size + pad * 2), "white")
        backing.paste(logo, (pad, pad), logo)
        position = ((size - backing.width) // 2, (size - backing.height) // 2)
        img.paste(backing, position, backing)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def generate_qr_svg(data: str, *, error_correction: str = "M") -> bytes:
    img = qrcode.make(
        data, image_factory=qrcode.image.svg.SvgPathImage, error_correction=_validated_level(error_correction)
    )
    buffer = io.BytesIO()
    img.save(buffer)
    return buffer.getvalue()


async def upload_logo(file: UploadFile) -> str:
    """Saves the uploaded logo and returns its filename (the opaque logo_id)."""
    content_type = file.content_type or ""
    if content_type not in ALLOWED_LOGO_TYPES:
        raise UnsupportedLogoTypeError("Only PNG, JPEG, or WEBP images are allowed")

    contents = await file.read()
    if len(contents) > MAX_LOGO_BYTES:
        raise LogoTooLargeError("Logo must be 1MB or smaller")

    QR_LOGO_DIR.mkdir(parents=True, exist_ok=True)
    extension = ALLOWED_LOGO_TYPES[content_type]
    filename = f"{uuid.uuid4().hex}{extension}"
    (QR_LOGO_DIR / filename).write_bytes(contents)
    return filename


def logo_path_for(logo_id: str) -> Path | None:
    if not _LOGO_FILENAME_PATTERN.match(logo_id):
        return None
    candidate = QR_LOGO_DIR / logo_id
    return candidate if candidate.is_file() else None
