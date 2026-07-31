import secrets

import pyotp

ISSUER = "NeuroDesk AI"


def generate_secret() -> str:
    return pyotp.random_base32()


def build_otpauth_url(*, secret: str, account_email: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=account_email, issuer_name=ISSUER)


def verify_code(*, secret: str, code: str) -> bool:
    return pyotp.totp.TOTP(secret).verify(code.strip(), valid_window=1)


def generate_recovery_codes(count: int = 8) -> list[str]:
    return [secrets.token_hex(4) for _ in range(count)]
