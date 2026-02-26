class HarpocratesError(Exception):
    """Base exception for all Harpocrates errors."""
    pass

class AuthenticationError(HarpocratesError):
    """Raised when the master password or secret key is incorrect."""
    pass

class VaultCorruptError(HarpocratesError):
    """Raised when the vault file is tampered with or corrupted."""
    pass

class VaultNotFoundError(HarpocratesError):
    """Raised when attempting to load a non-existent vault."""
    pass