import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from argon2.low_level import hash_secret_raw, Type

class HarpocratesCrypto:
    def __init__(self):
        self.ARGON2_ITERATIONS = 4
        self.ARGON2_MEMORY = 65536  
        self.ARGON2_PARALLELISM = 4
        self.KEY_LEN = 32          

    def derive_key(self, master_password: str, secret_key: str, salt: bytes) -> bytes:
        """
        Deriva una clave combinando la contraseña maestra y la Secret Key.
        Nivel Senior: Evita colisiones y maximiza la entropía.
        """
        combined_secret = f"{master_password}:{secret_key}".encode('utf-8')
        
        return hash_secret_raw(
            secret=combined_secret,
            salt=salt,
            time_cost=self.ARGON2_ITERATIONS,
            memory_cost=self.ARGON2_MEMORY,
            parallelism=self.ARGON2_PARALLELISM,
            hash_len=self.KEY_LEN,
            type=Type.ID
        )

    def generate_secret_key(self) -> str:
        """Genera una Secret Key de alta entropía (formato amigable tipo: XXXX-XXXX-XXXX)."""
        import secrets
        import string
        alphabet = string.ascii_uppercase + string.digits
        parts = [''.join(secrets.choice(alphabet) for _ in range(4)) for _ in range(4)]
        return '-'.join(parts)

    def encrypt(self, data: bytes, key: bytes) -> bytes:
        """Cifra usando AES-256-GCM con un Nonce único."""
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)  
        ciphertext = aesgcm.encrypt(nonce, data, None)
        return nonce + ciphertext  

    def decrypt(self, encrypted_data: bytes, key: bytes) -> bytes:
        """Descifra y verifica la integridad de los datos."""
        aesgcm = AESGCM(key)
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        return aesgcm.decrypt(nonce, ciphertext, None)