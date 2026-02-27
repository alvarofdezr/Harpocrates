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
        """Prepares a clean environment before each test."""
        self.test_vault_file = "test_vault.hpro"
        self.test_backup_file = "test_vault_backup.hpro"
        self.test_csv_file = "test_import.csv"
        self.m_pass = "TestPass123!"
        
        self.crypto = HarpocratesCrypto()
        self.s_key = self.crypto.generate_secret_key()
        self.vault = VaultManager(self.test_vault_file)
        
        self.vault.create_new_vault(self.m_pass, self.s_key)

    def tearDown(self):
        """Cleans up temporary files after each test."""
        files_to_clean = [
            self.test_vault_file, 
            self.test_backup_file, 
            self.test_csv_file,
            self.test_vault_file + ".tmp"
        ]
        for file in files_to_clean:
            if os.path.exists(file):
                os.remove(file)
        PasswordAuditor.clear_cache()

    def test_add_entry_stores_data_correctly(self):
        """Tests that entries can be added and read safely from memory."""
        self.vault.add_entry("Netflix", "user@test.com", "pass123", "http://netflix.com", "My notes")
        
        entry = self.vault.get_entries()[0]
        
        self.assertEqual(entry['title'], "Netflix")
        self.assertEqual(entry['password'], "pass123")
        self.assertEqual(entry['notes'], "My notes")

    def test_update_entry_modifies_existing_data(self):
        """Tests updating existing entries without master keys."""
        self.vault.add_entry("Facebook", "old_user", "old_pass")
        
        changes = {
            "username": "new_user_pro",
            "password": "NEW_PASSWORD_SECURE"
        }
        self.vault.update_entry(0, changes)

        updated_entry = self.vault.get_entries()[0]
        
        self.assertEqual(updated_entry['username'], "new_user_pro")
        self.assertEqual(updated_entry['title'], "Facebook")

    def test_delete_entry_removes_item(self):
        """Tests deleting entries securely."""
        self.vault.add_entry("Twitter", "u1", "p1")
        self.vault.add_entry("Google", "u2", "p2")
        
        self.vault.delete_entry(0)
        
        entries = self.vault.get_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['title'], "Google")

    def test_backup_mechanism_creates_valid_copy(self):
        """Critical test: Simulates the backup system and loads it."""
        self.vault.add_entry("DataCritical", "admin", "supersecret")
        
        shutil.copy(self.test_vault_file, self.test_backup_file)
        self.assertTrue(os.path.exists(self.test_backup_file))

        backup_vault = VaultManager(self.test_backup_file)
        backup_vault.load_vault(self.m_pass, self.s_key)
        
        self.assertEqual(backup_vault.get_entries()[0]['title'], "DataCritical")

    def test_vault_file_is_encrypted_and_not_plaintext(self):
        """Verifies that the file on disk is NOT plain text (JSON)."""
        self.vault.add_entry("SecretService", "admin", "123456")
        
        with open(self.test_vault_file, 'rb') as f:
            content = f.read()
            
        self.assertNotIn(b"SecretService", content)
        self.assertNotEqual(content[0:1], b'{')

    def test_audit_logs_record_system_actions(self):
        """Verifies that the system logs every movement."""
        logs = self.vault.get_logs()
        self.assertTrue(len(logs) > 0)
        self.assertEqual(logs[-1]['action'], 'SYSTEM') 
        
        self.vault.add_audit_event("LOGIN", "Unit Test Access")
        self.assertEqual(self.vault.get_logs()[0]['action'], 'LOGIN') 
        
        self.vault.add_entry("LogTestApp", "user", "pass")
        self.assertEqual(self.vault.get_logs()[0]['action'], 'CREATE')
        self.assertIn("LogTestApp", self.vault.get_logs()[0]['details'])

        self.vault.update_entry(0, {"notes": "Edited"})
        self.assertEqual(self.vault.get_logs()[0]['action'], 'UPDATE')

        self.vault.delete_entry(0)
        self.assertEqual(self.vault.get_logs()[0]['action'], 'DELETE')

    def test_generator_creates_high_entropy_passwords(self):
        """Tests the high-entropy password generator over multiple iterations."""
        valid_symbols = "!@#$%^&*()-_=+" 
        
        for _ in range(10):
            pw = PasswordGenerator.generate(32)
            self.assertEqual(len(pw), 32)
            self.assertTrue(any(c.isupper() for c in pw), f"Missing uppercase in: {pw}")
            self.assertTrue(any(c.islower() for c in pw), f"Missing lowercase in: {pw}")
            self.assertTrue(any(c.isdigit() for c in pw), f"Missing digit in: {pw}")
            self.assertTrue(any(c in valid_symbols for c in pw), f"Missing valid symbol in: {pw}")

    @patch('core.auditor.requests.get')
    def test_hibp_auditor_respects_kanonymity(self, mock_get):
        """Tests the HaveIBeenPwned API integration using mocked K-Anonymity."""
        
        class MockResponse:
            def __init__(self, text, status_code):
                self.text = text
                self.status_code = status_code
            
            def raise_for_status(self):
                if self.status_code != 200:
                    raise Exception(f"HTTP Error: {self.status_code}")

        def side_effect(url, *args, **kwargs):
            if "5BAA6" in url:
                return MockResponse("1E4C9B93F3F0682250B6CF8331B7EE68FD8:2500\nOTHERHASH123:10", 200)
            
            if "5F4DC" in url:
                return MockResponse("ABCDEF1234567890ABCDEF1234567890ABCDE:5\nFFFFF9B93F3F0682250B6CF8331B7EE68FD8:2", 200)
                
            return MockResponse("", 200)

        mock_get.side_effect = side_effect

        pwned_count = PasswordAuditor.check_pwned("password")
        self.assertEqual(pwned_count, 2500)

        safe_count = PasswordAuditor.check_pwned("SafePassword123!")
        self.assertEqual(safe_count, 0)

    def test_csv_import_handles_duplicates(self):
        """Tests importing data from a CSV file with duplicate handling."""
        with open(self.test_csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["name", "url", "username", "password", "notes"])
            writer.writerow(["GitHub", "https://github.com", "dev1", "gitpass123", "work account"])
            writer.writerow(["Spotify", "", "music_fan", "spotpass", ""])
            writer.writerow(["GitHub", "https://github.com", "dev1", "gitpass123", "duplicate"])

        qty, msg = import_from_csv(self.test_csv_file, self.vault)

        self.assertEqual(qty, 2)
        entries = self.vault.get_entries()
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]['title'], "GitHub")
        self.assertEqual(entries[1]['title'], "Spotify")
        self.assertIn("Skipped 1 duplicates", msg)

    def test_log_integrity_detects_tampering(self):
        """Tests that the hash-chain correctly identifies modified intermediate logs."""
        self.vault.add_entry("Service1", "user1", "pass1")
        self.vault.add_entry("Service2", "user2", "pass2")
        
        self.vault._data['logs'][1]['details'] = "TAMPERED"
        
        self.assertFalse(self.vault.verify_log_integrity())

if __name__ == '__main__':
    unittest.main()