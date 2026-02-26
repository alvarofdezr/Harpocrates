import unittest
import os
import shutil
import csv
import sys
from unittest.mock import patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.vault import VaultManager
from core.crypto import HarpocratesCrypto
from core.generator import PasswordGenerator
from core.auditor import PasswordAuditor
from core.importer import import_from_csv

class TestHarpocratesCore(unittest.TestCase):

    def setUp(self):
        """
        Runs BEFORE each test.
        Prepares a clean environment: a fresh vault and new keys.
        """
        self.test_vault_file = "test_vault.hpro"
        self.test_backup_file = "test_vault_backup.hpro"
        self.test_csv_file = "test_import.csv"
        self.m_pass = "TestPass123!"
        
        self.crypto = HarpocratesCrypto()
        self.s_key = self.crypto.generate_secret_key()
        self.vault = VaultManager(self.test_vault_file)
        
        self.vault.create_new_vault(self.m_pass, self.s_key)

    def tearDown(self):
        """
        Runs AFTER each test.
        Cleans up the mess: deletes all temporary files.
        """
        for file in [self.test_vault_file, self.test_backup_file, self.test_csv_file]:
            if os.path.exists(file):
                os.remove(file)

    def test_1_add_entry(self):
        """Tests that entries can be added and read from memory."""
        self.vault.add_entry(self.m_pass, self.s_key, "Netflix", "user@test.com", "pass123", "http://netflix.com", "My notes")
        
        entry = self.vault.data['entries'][0]
        
        self.assertEqual(entry['title'], "Netflix")
        self.assertEqual(entry['password'], "pass123")
        self.assertEqual(entry['notes'], "My notes")

    def test_2_update_entry(self):
        """Tests updating entries."""
        self.vault.add_entry(self.m_pass, self.s_key, "Facebook", "old_user", "old_pass")
        
        changes = {
            "username": "new_user_pro",
            "password": "NEW_PASSWORD_SECURE"
        }
        self.vault.update_entry(self.m_pass, self.s_key, 0, changes)

        updated_entry = self.vault.data['entries'][0]
        
        self.assertEqual(updated_entry['username'], "new_user_pro")
        self.assertEqual(updated_entry['title'], "Facebook")

    def test_3_delete_entry(self):
        """Tests deleting entries."""
        self.vault.add_entry(self.m_pass, self.s_key, "Twitter", "u1", "p1")
        self.vault.add_entry(self.m_pass, self.s_key, "Google", "u2", "p2")
        
        self.vault.delete_entry(self.m_pass, self.s_key, 0)
        
        self.assertEqual(len(self.vault.data['entries']), 1)
        self.assertEqual(self.vault.data['entries'][0]['title'], "Google")

    def test_4_backup_mechanism(self):
        """Critical test: Simulates the backup system."""
        self.vault.add_entry(self.m_pass, self.s_key, "DataCritical", "admin", "supersecret")
        
        shutil.copy(self.test_vault_file, self.test_backup_file)
        self.assertTrue(os.path.exists(self.test_backup_file))

        backup_vault = VaultManager(self.test_backup_file)
        data = backup_vault.load_vault(self.m_pass, self.s_key)
        
        self.assertEqual(data['entries'][0]['title'], "DataCritical")

    def test_5_encryption_security(self):
        """Verifies that the file on disk is NOT plain text (JSON)."""
        self.vault.add_entry(self.m_pass, self.s_key, "SecretService", "admin", "123456")
        
        with open(self.test_vault_file, 'rb') as f:
            content = f.read()
            
        self.assertNotIn(b"SecretService", content)
        self.assertNotEqual(content[0:1], b'{')

    def test_6_audit_logs(self):
        """Verifies that the system logs every movement in memory."""
        self.assertIn('logs', self.vault.data)
        self.assertTrue(len(self.vault.data['logs']) > 0)
        self.assertEqual(self.vault.data['logs'][-1]['action'], 'SYSTEM') 
        
        self.vault.add_audit_event(self.m_pass, self.s_key, "LOGIN", "Unit Test Access")
        self.assertEqual(self.vault.data['logs'][0]['action'], 'LOGIN') 
        
        self.vault.add_entry(self.m_pass, self.s_key, "LogTestApp", "user", "pass")
        self.assertEqual(self.vault.data['logs'][0]['action'], 'CREATE')
        self.assertIn("LogTestApp", self.vault.data['logs'][0]['details'])

        self.vault.update_entry(self.m_pass, self.s_key, 0, {"notes": "Edited"})
        self.assertEqual(self.vault.data['logs'][0]['action'], 'UPDATE')

        self.vault.delete_entry(self.m_pass, self.s_key, 0)
        self.assertEqual(self.vault.data['logs'][0]['action'], 'DELETE')

    def test_7_password_generator(self):
        """Tests the high-entropy password generator."""
        pw = PasswordGenerator.generate(32)
        self.assertEqual(len(pw), 32)
        self.assertTrue(any(c.isupper() for c in pw))
        self.assertTrue(any(c.isdigit() for c in pw))
        self.assertTrue(any(c in "!@#$%^&*" for c in pw))

    @patch('core.auditor.requests.get')
    def test_8_hibp_auditor(self, mock_get):
        """Tests the HaveIBeenPwned API integration using K-Anonymity (Mocked)."""
        
        class MockResponse:
            def __init__(self, text, status_code):
                self.text = text
                self.status_code = status_code
            
            def raise_for_status(self):
                if self.status_code != 200:
                    raise Exception(f"HTTP Error: {self.status_code}")

        def side_effect(url, *args, **kwargs):
            if "5BAA6" in url:
                return MockResponse("1E4C9B93F3F0682250B6CF8331B7EE68FD8:2500\nOTHER:10", 200)
            return MockResponse("SOMEOTHERHASH:5\n", 200)

        mock_get.side_effect = side_effect

        pwned_count = PasswordAuditor.check_pwned("password")
        self.assertEqual(pwned_count, 2500)

        safe_pw = PasswordGenerator.generate(32)
        safe_count = PasswordAuditor.check_pwned(safe_pw)
        self.assertEqual(safe_count, 0)

    def test_9_csv_import(self):
        """Tests importing data from a CSV file with duplicate handling."""
        with open(self.test_csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["name", "url", "username", "password", "notes"])
            writer.writerow(["GitHub", "https://github.com", "dev1", "gitpass123", "work account"])
            writer.writerow(["Spotify", "", "music_fan", "spotpass", ""])
            writer.writerow(["GitHub", "https://github.com", "dev1", "gitpass123", "duplicate"])

        qty, msg = import_from_csv(self.test_csv_file, self.vault, self.s_key, self.m_pass)

        self.assertEqual(qty, 2) 
        self.assertEqual(len(self.vault.data['entries']), 2)
        self.assertEqual(self.vault.data['entries'][0]['title'], "GitHub")
        self.assertEqual(self.vault.data['entries'][1]['title'], "Spotify")
        self.assertIn("Skipped 1 duplicates", msg)

if __name__ == '__main__':
    unittest.main()