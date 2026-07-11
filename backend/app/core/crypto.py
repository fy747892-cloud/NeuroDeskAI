from cryptography.fernet import Fernet

from app.core.config import settings

_fernet = Fernet(settings.token_encryption_key.encode("utf-8"))


def encrypt_token(plain: str) -> str:
    return _fernet.encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt_token(cipher: str) -> str:
    return _fernet.decrypt(cipher.encode("utf-8")).decode("utf-8")
