import secrets
import string

class PasswordGenerator:
    @staticmethod
    def generate(length=20):
        """
        Generates a cryptographically secure random password.
        Includes uppercase, lowercase, digits, and symbols.
        """
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
        return ''.join(secrets.choice(alphabet) for _ in range(length))