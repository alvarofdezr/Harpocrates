import json
import os
from datetime import datetime
from core.crypto import HarpocratesCrypto

class VaultManager:
    def __init__(self, vault_path="vault.hpro"):
        self.vault_path = vault_path
        self.crypto = HarpocratesCrypto()
        self.data = None 

    def create_new_vault(self, master_password, secret_key):
        """Creates a v1.5 vault with audit logging support."""
        empty_data = {
            "version": "1.5",
            "created_at": datetime.now().isoformat(),
            "entries": [],
            "logs": [] 
        }
        self.data = empty_data
        self._append_log("SYSTEM", "Vault Created")
        self.save_vault(master_password, secret_key)

    def save_vault(self, master_password, secret_key):
        """Encrypts and saves the current state of self.data to disk."""
        if self.data is None:
            return
        json_str = json.dumps(self.data)
        encrypted_data = self.crypto.encrypt_data(json_str, master_password, secret_key)
        with open(self.vault_path, 'wb') as f:
            f.write(encrypted_data)

    def load_vault(self, master_password, secret_key):
        """Reads from disk, decrypts, and stores in self.data."""
        if not os.path.exists(self.vault_path):
            raise FileNotFoundError("Vault file not found.")
            
        with open(self.vault_path, 'rb') as f:
            encrypted_data = f.read()
            
        decrypted_json = self.crypto.decrypt_data(encrypted_data, master_password, secret_key)
        self.data = json.loads(decrypted_json)

        # --- AUTOMATIC MIGRATION v1.4 -> v1.5 ---
        if isinstance(self.data, dict) and self.data.get("version") == "1.4":
            self.data['version'] = "1.5"
            self._append_log("SYSTEM", "Upgraded to v1.5 (Enhanced Security)")
            self.save_vault(master_password, secret_key)
            
        return self.data

    def _append_log(self, action, details):
        """Writes to the internal (private) log using self.data."""
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action.upper(),
            "details": details
        }

        if 'logs' not in self.data: 
            self.data['logs'] = []
        self.data['logs'].insert(0, log_entry)

    def add_audit_event(self, master_password, secret_key, action, details):
        """Registers external events (Login, Backup, HIBP Scan)."""
        self._append_log(action, details)
        self.save_vault(master_password, secret_key)

    def add_entry(self, master_password, secret_key, app_name, username, password, url="", notes=""):
        """Adds a new credential entry to the vault."""
        new_entry = {
            "title": app_name, "username": username, "password": password,
            "url": url, "notes": notes, "created_at": datetime.now().isoformat()
        }
        if 'entries' not in self.data: 
            self.data['entries'] = []
        self.data['entries'].append(new_entry)
        
        self._append_log("CREATE", f"Entry added: {app_name}")
        
        self.save_vault(master_password, secret_key)
        return True

    def delete_entry(self, master_password, secret_key, index):
        """Deletes an entry by index."""
        try:
            removed = self.data['entries'].pop(index)
            self._append_log("DELETE", f"Entry removed: {removed['title']}")
            self.save_vault(master_password, secret_key)
            return True, f"Deleted: {removed['title']}"
        except IndexError:
            return False, "Index error."

    def update_entry(self, master_password, secret_key, index, new_data):
        """Updates an existing entry."""
        try:
            entry = self.data['entries'][index]
            original_title = entry['title']
            
            for k, v in new_data.items():
                if v: entry[k] = v
            
            entry['updated_at'] = datetime.now().isoformat()

            self._append_log("UPDATE", f"Modified: {original_title}")
            
            self.save_vault(master_password, secret_key)
            return True, "Updated successfully."
        except IndexError:
            return False, "Index error."