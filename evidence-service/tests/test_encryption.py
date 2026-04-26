import unittest
from src.services.encryption import encrypt_file, decrypt_file
from cryptography.fernet import Fernet

class TestEncryption(unittest.TestCase):

    def setUp(self):
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
        self.test_data = b'This is a test.'
        self.encrypted_data = self.cipher.encrypt(self.test_data)

    def test_encrypt_file(self):
        encrypted = encrypt_file(self.test_data, self.key)
        self.assertIsNotNone(encrypted)
        self.assertNotEqual(encrypted, self.test_data)

    def test_decrypt_file(self):
        decrypted = decrypt_file(self.encrypted_data, self.key)
        self.assertEqual(decrypted, self.test_data)

    def test_encrypt_decrypt_round_trip(self):
        encrypted = encrypt_file(self.test_data, self.key)
        decrypted = decrypt_file(encrypted, self.key)
        self.assertEqual(decrypted, self.test_data)

if __name__ == '__main__':
    unittest.main()