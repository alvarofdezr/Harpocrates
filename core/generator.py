import secrets
import string

class PasswordGenerator:
    @staticmethod
    def generate(length=20):
        """
        Generates a cryptographically secure random password.
        Guarantees at least one uppercase, lowercase, digit, and symbol.
        """
        symbols = "!@#$%^&*()-_=+"
        alphabet = string.ascii_letters + string.digits + symbols
        
        password = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice(symbols)
        ]
        
        password += [secrets.choice(alphabet) for _ in range(length - 4)]
        
        secure_rng = secrets.SystemRandom()
        secure_rng.shuffle(password)
        
        return ''.join(password)