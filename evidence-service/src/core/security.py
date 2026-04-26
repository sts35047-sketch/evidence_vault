from cryptography.fernet import Fernet
import os

def generate_key():
    return Fernet.generate_key().decode()

def get_fernet_key():
    return os.environ.get('FERNET_KEY', generate_key())

def encrypt_data(data):
    fernet = Fernet(get_fernet_key())
    return fernet.encrypt(data.encode())

def decrypt_data(encrypted_data):
    fernet = Fernet(get_fernet_key())
    return fernet.decrypt(encrypted_data).decode()