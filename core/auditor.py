import hashlib
import requests

class PasswordAuditor:
    _cache = {}

    @staticmethod
    def check_pwned(password: str) -> int:
        """Checks if a password has been leaked using HIBP K-Anonymity."""
        
        sha1_password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper() # nosec - SHA1 is required by HIBP API for K-Anonymity, not used for cryptographic storage
        
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
            
        except requests.RequestException:
            return 0