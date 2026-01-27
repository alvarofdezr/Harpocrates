import unittest
from core.crypto import HarpocratesCrypto

class TestHarpocratesCrypto(unittest.TestCase):
    def setUp(self):
        self.crypto = HarpocratesCrypto()

    def test_encryption_decryption(self):
        key = b"0" * 32 
        original_data = b"Dato secreto 123"
        
        encrypted = self.crypto.encrypt(original_data, key)
        decrypted = self.crypto.decrypt(encrypted, key)
        
        self.assertEqual(original_data, decrypted)

if __name__ == '__main__':
    unittest.main()