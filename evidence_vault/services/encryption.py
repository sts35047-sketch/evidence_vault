# New: encryption helpers for file at rest (Fernet)
import os
from cryptography.fernet import Fernet, InvalidToken

from evidence_vault.core.config import settings

FERNET_KEY = os.environ.get('FERNET_KEY')

def get_fernet():
    key = settings.fernet_key
    if not key:
        return None
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)

def encrypt_bytes(data: bytes) -> bytes:
    f = get_fernet()
    return f.encrypt(data) if f else data

def decrypt_bytes(data: bytes) -> bytes:
    f = get_fernet()
    return f.decrypt(data) if f else data
