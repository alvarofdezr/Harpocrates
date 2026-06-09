import os
import secrets
from typing import Union
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from core.exceptions import AuthenticationError, VaultCorruptError
from core.config import config

class HarpocratesCrypto:
    def __init__(self) -> None:
        self.salt_size: int = config.salt_size
        self.nonce_size: int = config.aes_nonce_size
        self.key_len: int = config.aes_key_size

    def generate_secret_key(self) -> str:
        """Generates a random 32-byte Secret Key in URL-safe base64."""
        return secrets.token_urlsafe(32)

    def derive_session_key(self, master_password: str, secret_key: str, salt: bytes) -> bytes:
        """Derives the AES-GCM key using Argon2id."""
        combined_pass = (master_password + secret_key).encode('utf-8')
        kdf = Argon2id(
            salt=salt, 
            length=self.key_len, 
            iterations=config.argon2_iterations,
            lanes=config.argon2_lanes, 
            memory_cost=config.argon2_memory_cost, 
            ad=None, 
            secret=None
        )
        return kdf.derive(combined_pass)

    def encrypt_with_session_key(self, plaintext_data: Union[str, bytes], session_key: bytes, salt: bytes) -> bytes:
        """Encrypts using the in-memory session key (Fast AES-GCM)."""
        if isinstance(plaintext_data, str):
            plaintext_data = plaintext_data.encode('utf-8')
            
        nonce = secrets.token_bytes(self.nonce_size)
        aesgcm = AESGCM(session_key)
        ciphertext = aesgcm.encrypt(nonce, plaintext_data, None)
        return salt + nonce + ciphertext

    def decrypt_with_session_key(self, encrypted_bytes: bytes, session_key: bytes, salt: bytes) -> str:
        """Decrypts using the in-memory session key."""
        try:
            nonce = encrypted_bytes[self.salt_size : self.salt_size + self.nonce_size]
            ciphertext = encrypted_bytes[self.salt_size + self.nonce_size :]
            
            aesgcm = AESGCM(session_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode('utf-8')
        except InvalidTag as e:
            raise AuthenticationError("Authentication failed or vault is corrupted.") from e
        except Exception as e:
            raise VaultCorruptError(f"Unexpected data corruption: {e}") from e