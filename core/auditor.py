import hashlib
import requests

class PasswordAuditor:
    @staticmethod
    def check_pwned(password):
        """
        Checks if a password has been exposed in data breaches.
        Uses K-Anonymity (API Range) for total privacy.
        
        Returns:
            int: Number of times it has been leaked.
            -1: Connection error.
        """

        sha1_password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper() #nosec
        prefix, suffix = sha1_password[:5], sha1_password[5:]
        
        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            hashes = (line.split(':') for line in response.text.splitlines())
            
            for h, count in hashes:
                if h == suffix:
                    return int(count)
            
            return 0 
            
        except requests.RequestException:
            return -1 