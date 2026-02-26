import json
import os
from datetime import datetime
from core.crypto import HarpocratesCrypto
from core.exceptions import VaultNotFoundError

class VaultManager:
    def __init__(self, vault_path="vault.hpro"):
        self.vault_path = vault_path
        self.crypto = HarpocratesCrypto()
        self._data = None
        self._session_key = None
        self._salt = None

    def create_new_vault(self, master_password, secret_key):
        self._salt = os.urandom(self.crypto.salt_size)
        self._session_key = self.crypto.derive_session_key(master_password, secret_key, self._salt)
        self._data = {"version": "1.5.1", "created_at": datetime.now().isoformat(), "entries": [], "logs": []}
        self._append_log("SYSTEM", "Vault Created")
        self.save_vault()

    def load_vault(self, master_password, secret_key):
        if not os.path.exists(self.vault_path):
            raise VaultNotFoundError(f"The vault file '{self.vault_path}' could not be found.")
            
        with open(self.vault_path, 'rb') as f:
            encrypted_data = f.read()
            
        self._salt = encrypted_data[:self.crypto.salt_size]
        self._session_key = self.crypto.derive_session_key(master_password, secret_key, self._salt)
        
        decrypted_json = self.crypto.decrypt_with_session_key(encrypted_data, self._session_key, self._salt)
        self._data = json.loads(decrypted_json)
        return True

    def save_vault(self):
        """Saves data instantly without re-deriving Argon2id."""
        if self._data is None or self._session_key is None:
            return
        json_str = json.dumps(self._data)
        encrypted_data = self.crypto.encrypt_with_session_key(json_str, self._session_key, self._salt)
        with open(self.vault_path, 'wb') as f:
            f.write(encrypted_data)

    def get_entries(self):
        """Encapsulates public data access."""
        return self._data.get('entries', [])

    def get_logs(self):
        """Encapsulates log access."""
        return self._data.get('logs', [])

    def _append_log(self, action, details):
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action.upper(),
            "details": details
        }
        if 'logs' not in self._data: self._data['logs'] = []
        self._data['logs'].insert(0, log_entry)

    def add_audit_event(self, action, details):
        self._append_log(action, details)
        self.save_vault()

    def add_entry(self, app_name, username, password, url="", notes=""):
        new_entry = {
            "title": app_name, "username": username, "password": password,
            "url": url, "notes": notes, "created_at": datetime.now().isoformat()
        }
        self._data['entries'].append(new_entry)
        self._append_log("CREATE", f"Entry added: {app_name}")
        self.save_vault()
        return True
    
    def add_entries_bulk(self, new_entries_data: list) -> bool:
        """Adds multiple entries in a single transaction with rollback capability."""
        if not new_entries_data:
            return True
            
        original_entries = [dict(e) for e in self._data.get('entries', [])]
        original_logs = [dict(l) for l in self._data.get('logs', [])]
        
        try:
            for item in new_entries_data:
                new_entry = {
                    "title": item['title'], "username": item['username'], "password": item['password'],
                    "url": item.get('url', ''), "notes": item.get('notes', ''), "created_at": datetime.now().isoformat()
                }
                self._data['entries'].append(new_entry)
                
            self._append_log("IMPORT", f"Bulk imported {len(new_entries_data)} entries")
            
            self.save_vault()
            return True
            
        except Exception as e:
            self._data['entries'] = original_entries
            self._data['logs'] = original_logs
            raise Exception(f"Bulk import failed, changes rolled back: {str(e)}")

    def delete_entry(self, index):
        try:
            removed = self._data['entries'].pop(index)
            self._append_log("DELETE", f"Entry removed: {removed['title']}")
            self.save_vault()
            return True
        except IndexError:
            return False

    def update_entry(self, index, new_data):
        try:
            entry = self._data['entries'][index]
            for k, v in new_data.items():
                if v: entry[k] = v
            entry['updated_at'] = datetime.now().isoformat()
            self._append_log("UPDATE", f"Modified: {entry['title']}")
            self.save_vault()
            return True
        except IndexError:
            return False