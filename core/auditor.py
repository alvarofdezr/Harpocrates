import hashlib
import requests
from core.exceptions import HIBPConnectionError

class PasswordAuditor:
    _cache = {}

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the cache (Useful for test idempotency)."""
        cls._cache.clear()

    @staticmethod
    def check_pwned(password: str) -> int:
        """Checks if a password has been leaked using HIBP K-Anonymity."""
        
        # nosec - SHA1 is strictly required by HIBP API for K-Anonymity
        sha1_password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper() # nosec
        
        prefix = sha1_password[:5]
        suffix = sha1_password[5:]

        if sha1_password in PasswordAuditor._cache:
            return PasswordAuditor._cache[sha1_password]

        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        headers = {"User-Agent": "Harpocrates-Vault-Security-Auditor"}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            hashes = (line.split(':') for line in response.text.splitlines())
            for h, count in hashes:
                if h == suffix:
                    PasswordAuditor._cache[sha1_password] = int(count)
                    return int(count)
                    
            PasswordAuditor._cache[sha1_password] = 0
            return 0
        except requests.RequestException as e:
            raise HIBPConnectionError(f"Failed to connect to HIBP API: {e}") from e