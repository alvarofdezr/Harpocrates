import secrets
import string

class PasswordGenerator:
    @staticmethod
    def generate(length=20):
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
        return ''.join(secrets.choice(alphabet) for _ in range(length))