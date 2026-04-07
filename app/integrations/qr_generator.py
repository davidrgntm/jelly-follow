"""QR code generation using qrcode library."""
import io
import os
import logging
import qrcode
from qrcode.image.styledpil import StyledPilImage
from PIL import Image

logger = logging.getLogger(__name__)
QR_DIR = "static/qr"


def generate_qr_image(data: str, filename: str) -> str:
    os.makedirs(QR_DIR, exist_ok=True)
    filepath = os.path.join(QR_DIR, filename)
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a1a2e", back_color="white")
    img.save(filepath)
    logger.info("QR image saved: %s", filepath)
    return filepath


def generate_qr_bytes(data: str) -> bytes:
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a1a2e", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
