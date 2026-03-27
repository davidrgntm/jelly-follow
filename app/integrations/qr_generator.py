"""
QR code generation module.
"""
import io
import os
import qrcode
from qrcode.image.styledpil import StyledPilImage
from PIL import Image


QR_DIR = "static/qr"


def ensure_qr_dir():
    os.makedirs(QR_DIR, exist_ok=True)


def generate_qr_image(url: str, filename: str) -> str:
    """
    Generate QR code PNG image and save to static/qr/.
    Returns relative path to the file.
    """
    ensure_qr_dir()

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    filepath = os.path.join(QR_DIR, filename)
    img.save(filepath)
    return filepath


def generate_qr_bytes(url: str) -> bytes:
    """Generate QR and return as bytes (for sending via Telegram)."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()
