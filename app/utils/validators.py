import re
from typing import Optional


VALID_COUNTRIES = {"UZ", "RU", "KG", "AZ"}
VALID_LANGUAGES = {"uz", "ru", "en", "kg", "az"}
VALID_ROLES = {"employee", "ga", "super_admin"}


def validate_country_code(code: str) -> bool:
    return code.upper() in VALID_COUNTRIES


def validate_language_code(code: str) -> bool:
    return code.lower() in VALID_LANGUAGES


def validate_phone(phone: str) -> Optional[str]:
    """Normalize and validate phone number."""
    digits = re.sub(r"[^\d+]", "", phone)
    if len(digits) >= 7:
        return digits
    return None


def normalize_phone(phone: str) -> str:
    return re.sub(r"[^\d+]", "", phone)
