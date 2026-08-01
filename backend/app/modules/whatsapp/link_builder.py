import urllib.parse

MIN_PHONE_DIGITS = 8


def normalize_phone_for_whatsapp(raw_phone: str) -> str | None:
    """Strip everything but digits so the number fits wa.me's expected format.

    Country-code correctness is assumed, not verified -- best effort only. Returns
    None when too few digits remain to plausibly be a phone number.
    """
    digits = "".join(ch for ch in raw_phone if ch.isdigit())
    if len(digits) < MIN_PHONE_DIGITS:
        return None
    return digits


def build_whatsapp_deep_link(*, phone_digits: str, body: str) -> str:
    return f"https://wa.me/{phone_digits}?text={urllib.parse.quote(body)}"
