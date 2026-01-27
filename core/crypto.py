import os
import base64
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, kdf

class HarpocratesCrypto:
    def __init__(self):
        self.salt_size = 16
        self.nonce_size = 12
        self.key_len = 32
        
    def generate_secret_key(self):
        """Genera una Secret Key aleatoria de 32 bytes en base64."""
        return base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')

    def _derive_key(self, master_password, secret_key, salt):
        """
        Deriva una clave de cifrado fuerte usando:
        1. Master Password (del usuario)
        2. Secret Key (del archivo/sistema)
        3. Salt (aleatorio por archivo)
        """
        combined_pass = (master_password + secret_key).encode('utf-8')
        
        kdf = Argon2id(
            salt=salt,
            length=self.key_len,
            iterations=4,     
            lanes=4,
            memory_cost=64 * 1024, 
            ad=None,
            secret=None
        )
        return kdf.derive(combined_pass)

    def encrypt_data(self, plaintext_data, master_password, secret_key):
        """
        Cifra datos (string) devolviendo bytes:
        Formato: [SALT (16)] + [NONCE (12)] + [CIPHERTEXT]
        """
        if not isinstance(plaintext_data, bytes):
            plaintext_data = plaintext_data.encode('utf-8')

        salt = os.urandom(self.salt_size)
        nonce = os.urandom(self.nonce_size)
        
        key = self._derive_key(master_password, secret_key, salt)
        
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext_data, None)
        
        return salt + nonce + ciphertext

    def decrypt_data(self, encrypted_bytes, master_password, secret_key):
        """
        Descifra bytes devolviendo string original.
        Extrae Salt y Nonce del propio paquete.
        """
        try:
            salt = encrypted_bytes[:self.salt_size]
            nonce = encrypted_bytes[self.salt_size : self.salt_size + self.nonce_size]
            ciphertext = encrypted_bytes[self.salt_size + self.nonce_size :]
            
            key = self._derive_key(master_password, secret_key, salt)
            
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            
            return plaintext.decode('utf-8')
            
        except Exception as e:
            raise ValueError("Clave incorrecta o datos corruptos.") from e