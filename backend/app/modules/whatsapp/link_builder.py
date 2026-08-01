import urllib.parse

MIN_PHONE_DIGITS = 8
TURKISH_MOBILE_LOCAL_LENGTH = 11  # "0" + 10-digit local number, e.g. 05551234567
TURKISH_MOBILE_BARE_LENGTH = 10  # no leading 0, no country code, e.g. 5551234567
TURKISH_COUNTRY_CODE = "90"


def normalize_phone_for_whatsapp(raw_phone: str) -> str | None:
    """Strip everything but digits so the number fits wa.me's expected format.

    wa.me requires the full international number with no leading "0" and no "+".
    Turkish numbers are commonly stored either as "0555..." (leading trunk zero,
    no country code) or "555..." (no zero, no country code either) -- both are
    otherwise-valid-looking digit strings that silently resolve to nothing on
    wa.me, so this rewrites them to "90555..." before falling through to the
    generic digits-only case. This is a Turkey-specific heuristic, not full
    E.164 parsing -- country-code correctness for non-Turkish numbers is still
    assumed, not verified.
    """
    digits = "".join(ch for ch in raw_phone if ch.isdigit())
    if len(digits) == TURKISH_MOBILE_LOCAL_LENGTH and digits.startswith("0"):
        digits = TURKISH_COUNTRY_CODE + digits[1:]
    elif len(digits) == TURKISH_MOBILE_BARE_LENGTH and digits.startswith("5"):
        digits = TURKISH_COUNTRY_CODE + digits
    if len(digits) < MIN_PHONE_DIGITS:
        return None
    return digits


def build_whatsapp_deep_link(*, phone_digits: str, body: str) -> str:
    return f"https://wa.me/{phone_digits}?text={urllib.parse.quote(body)}"
