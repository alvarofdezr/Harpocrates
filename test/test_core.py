import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.generator import PasswordGenerator

class TestHarpocrates(unittest.TestCase):

    def test_generator_length(self):
        """Comprueba que si pedimos 20 caracteres, nos da 20."""
        password = PasswordGenerator.generate(20)
        self.assertEqual(len(password), 20)

    def test_generator_strength(self):
        """Comprueba que la contraseña no está vacía."""
        password = PasswordGenerator.generate(12)
        self.assertTrue(len(password) > 0)
        self.assertTrue(isinstance(password, str))

if __name__ == '__main__':
    unittest.main()