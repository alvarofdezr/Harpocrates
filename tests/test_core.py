import unittest
import os
import shutil
import json
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.vault import VaultManager
from core.crypto import HarpocratesCrypto

class TestHarpocratesCore(unittest.TestCase):

    def setUp(self):
        """
        Se ejecuta ANTES de cada test.
        Prepara un entorno limpio: una bóveda nueva y claves frescas.
        """
        self.test_vault_file = "test_vault.hpro"
        self.test_backup_file = "test_vault_backup.hpro"
        self.m_pass = "TestPass123!"
        
        self.crypto = HarpocratesCrypto()
        self.s_key = self.crypto.generate_secret_key()
        self.vault = VaultManager(self.test_vault_file)
        
        self.vault.create_new_vault(self.m_pass, self.s_key)

    def tearDown(self):
        """
        Se ejecuta DESPUÉS de cada test.
        Limpia el desastre: borra los archivos creados.
        """
        if os.path.exists(self.test_vault_file):
            os.remove(self.test_vault_file)
        if os.path.exists(self.test_backup_file):
            os.remove(self.test_backup_file)

    def test_1_add_entry(self):
        """Prueba que se pueden añadir y leer entradas."""
        self.vault.add_entry(self.m_pass, self.s_key, "Netflix", "user@test.com", "pass123", "http://netflix.com", "Mis notas")
        
        data = self.vault.load_vault(self.m_pass, self.s_key)
        entry = data['entries'][0]
        
        self.assertEqual(entry['title'], "Netflix")
        self.assertEqual(entry['password'], "pass123")
        self.assertEqual(entry['notes'], "Mis notas")

    def test_2_update_entry(self):
        """Prueba la edición de entradas."""
        self.vault.add_entry(self.m_pass, self.s_key, "Facebook", "old_user", "old_pass")
        
        changes = {
            "username": "new_user_pro",
            "password": "NEW_PASSWORD_SECURE"
        }
        self.vault.update_entry(self.m_pass, self.s_key, 0, changes)

        data = self.vault.load_vault(self.m_pass, self.s_key)
        updated_entry = data['entries'][0]
        
        self.assertEqual(updated_entry['username'], "new_user_pro")
        self.assertEqual(updated_entry['title'], "Facebook")

    def test_3_delete_entry(self):
        """Prueba el borrado de entradas."""
        self.vault.add_entry(self.m_pass, self.s_key, "Twitter", "u1", "p1")
        self.vault.add_entry(self.m_pass, self.s_key, "Google", "u2", "p2")
        
        self.vault.delete_entry(self.m_pass, self.s_key, 0)
        
        data = self.vault.load_vault(self.m_pass, self.s_key)
        
        self.assertEqual(len(data['entries']), 1)
        self.assertEqual(data['entries'][0]['title'], "Google")

    def test_4_backup_mechanism(self):
        """Prueba crítica: Simula el sistema de backup."""
        self.vault.add_entry(self.m_pass, self.s_key, "DataCritical", "admin", "supersecret")
        
        shutil.copy(self.test_vault_file, self.test_backup_file)
        
        self.assertTrue(os.path.exists(self.test_backup_file))

        backup_vault = VaultManager(self.test_backup_file)
        data = backup_vault.load_vault(self.m_pass, self.s_key)
        
        self.assertEqual(data['entries'][0]['title'], "DataCritical")

    def test_5_encryption_security(self):
        """Verifica que el archivo en disco NO sea texto plano (JSON)."""
        self.vault.add_entry(self.m_pass, self.s_key, "SecretService", "admin", "123456")
        
        with open(self.test_vault_file, 'rb') as f:
            content = f.read()
            
        self.assertNotIn(b"SecretService", content)
        self.assertNotEqual(content[0:1], b'{')

    def test_6_audit_logs(self):
        """
        NUEVO (v1.3): Verifica que el sistema registre cada movimiento.
        """
        data = self.vault.load_vault(self.m_pass, self.s_key)
        self.assertIn('logs', data)
        self.assertTrue(len(data['logs']) > 0)
        self.assertEqual(data['logs'][-1]['action'], 'SYSTEM') 
        
        self.vault.add_audit_event(self.m_pass, self.s_key, "LOGIN", "Unit Test Access")
        data = self.vault.load_vault(self.m_pass, self.s_key)
        self.assertEqual(data['logs'][0]['action'], 'LOGIN') 
        
        self.vault.add_entry(self.m_pass, self.s_key, "LogTestApp", "user", "pass")
        data = self.vault.load_vault(self.m_pass, self.s_key)
        self.assertEqual(data['logs'][0]['action'], 'CREATE')
        self.assertIn("LogTestApp", data['logs'][0]['details'])

        self.vault.update_entry(self.m_pass, self.s_key, 0, {"notes": "Edited"})
        data = self.vault.load_vault(self.m_pass, self.s_key)
        self.assertEqual(data['logs'][0]['action'], 'UPDATE')

        self.vault.delete_entry(self.m_pass, self.s_key, 0)
        data = self.vault.load_vault(self.m_pass, self.s_key)
        self.assertEqual(data['logs'][0]['action'], 'DELETE')

if __name__ == '__main__':
    unittest.main()