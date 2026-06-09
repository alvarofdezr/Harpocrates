import os


class Settings:
    """
    Configuration management for Harpocrates Vault.
    Loads settings from environment variables or applies secure defaults.
    """
    def __init__(self) -> None:
        self.vault_path: str = os.getenv("VAULT_PATH", "vault.hpro")
        self.debug: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

        # Cryptography defaults based on OWASP recommendations
        self.argon2_memory_cost: int = int(os.getenv("ARGON2_MEMORY_COST", 64 * 1024))
        self.argon2_iterations: int = int(os.getenv("ARGON2_ITERATIONS", 4))
        self.argon2_lanes: int = int(os.getenv("ARGON2_LANES", 4))
        self.argon2_hash_len: int = int(os.getenv("ARGON2_HASH_LEN", 32))

        self.aes_key_size: int = int(os.getenv("AES_KEY_SIZE", 32))
        self.aes_nonce_size: int = int(os.getenv("AES_NONCE_SIZE", 12))
        self.salt_size: int = int(os.getenv("SALT_SIZE", 16))


config = Settings()
