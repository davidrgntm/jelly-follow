import re

VALID_COUNTRIES = {"UZ", "RU", "KG", "AZ"}
VALID_LANGUAGES = {"uz", "ru", "en", "kg", "az"}
VALID_ROLES = {"employee", "ga", "super_admin"}

def validate_country_code(code):
    return code.upper() in VALID_COUNTRIES

def validate_language_code(code):
    return code.lower() in VALID_LANGUAGES

def validate_phone(phone):
    digits = re.sub(r"[^\d+]", "", phone)
    if len(digits) >= 7:
        return digits
    return None

def normalize_phone(phone):
    return re.sub(r"[^\d+]", "", phone)
