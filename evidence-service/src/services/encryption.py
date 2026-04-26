from cryptography.fernet import Fernet
import os

class EncryptionService:
    def __init__(self):
        self.fernet_key = os.environ.get('FERNET_KEY')
        if not self.fernet_key:
            raise ValueError("FERNET_KEY environment variable not set.")
        self.fernet = Fernet(self.fernet_key.encode())

    def encrypt(self, data: bytes) -> bytes:
        return self.fernet.encrypt(data)

    def decrypt(self, token: bytes) -> bytes:
        return self.fernet.decrypt(token)