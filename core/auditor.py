from functools import lru_cache
import hashlib
import requests
from core.exceptions import HIBPConnectionError

class PasswordAuditor:
    @staticmethod
    @lru_cache(maxsize=512)
    def check_pwned(password: str) -> int:
        """Checks if a password has been leaked using HIBP K-Anonymity."""
        # nosec - SHA1 requerido por HIBP API para K-Anonymity
        sha1_password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()  # nosec
        
        prefix = sha1_password[:5]
        suffix = sha1_password[5:]

        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        headers = {"User-Agent": "Harpocrates-Vault-Security-Auditor"}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            for line in response.text.splitlines():
                h, _, count = line.partition(':')
                if h == suffix:
                    return int(count)
            return 0
        except requests.RequestException as e:
            raise HIBPConnectionError(f"Failed to connect to HIBP API: {e}") from e

    @classmethod
    def clear_cache(cls) -> None:
        cls.check_pwned.cache_clear()