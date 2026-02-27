import json
import os
import copy
import hashlib
from datetime import datetime
from core.crypto import HarpocratesCrypto
from core.exceptions import VaultNotFoundError

VERSION = "1.6.0"

class VaultManager:
    def __init__(self, vault_path: str = "vault.hpro") -> None:
        self.vault_path = os.path.abspath(vault_path)
        self.crypto = HarpocratesCrypto()
        self._data = None
        self._session_key = None
        self._salt = None

    def create_new_vault(self, master_password: str, secret_key: str) -> None:
        self._salt = os.urandom(self.crypto.salt_size)
        self._session_key = self.crypto.derive_session_key(master_password, secret_key, self._salt)
        self._data = {"version": VERSION, "created_at": datetime.now().isoformat(), "entries": [], "logs": []}
        self._append_log("SYSTEM", "Vault Created")
        self.save_vault()

    def load_vault(self, master_password: str, secret_key: str) -> bool:
        if not os.path.exists(self.vault_path):
            raise VaultNotFoundError(f"Vault file not found: {self.vault_path}")
            
        with open(self.vault_path, 'rb') as f:
            encrypted_data = f.read()
            
        self._salt = encrypted_data[:self.crypto.salt_size]
        self._session_key = self.crypto.derive_session_key(master_password, secret_key, self._salt)
        
        decrypted_json = self.crypto.decrypt_with_session_key(encrypted_data, self._session_key, self._salt)
        self._data = json.loads(decrypted_json)
        return True

    def save_vault(self) -> None:
        if self._data is None or self._session_key is None:
            return
            
        json_str = json.dumps(self._data)
        encrypted_data = self.crypto.encrypt_with_session_key(json_str, self._session_key, self._salt)
        
        tmp_path = self.vault_path + ".tmp"
        try:
            with open(tmp_path, 'wb') as f:
                f.write(encrypted_data)
                f.flush()
                os.fsync(f.fileno()) 
                
            os.replace(tmp_path, self.vault_path)
        except OSError:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    def get_entries(self) -> list:
        """Returns a deep copy to prevent external mutation of internal state."""
        return copy.deepcopy(self._data.get('entries', []))

    def get_logs(self) -> list:
        return copy.deepcopy(self._data.get('logs', []))

    def _append_log(self, action: str, details: str) -> None:
        """Appends a log entry using a cryptographic Hash-Chain for integrity."""
        prev_hash = "0" * 64
        if 'logs' not in self._data: 
            self._data['logs'] = []
            
        if len(self._data['logs']) > 0:
            last_log = self._data['logs'][0]
            last_log_str = json.dumps(last_log, sort_keys=True).encode('utf-8')
            prev_hash = hashlib.sha256(last_log_str).hexdigest()

        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action.upper(),
            "details": details,
            "prev_hash": prev_hash
        }
        self._data['logs'].insert(0, log_entry)

    def add_audit_event(self, action: str, details: str) -> None:
        self._append_log(action, details)
        self.save_vault()

    def add_entry(self, app_name: str, username: str, password: str, url: str = "", notes: str = "") -> bool:
        new_entry = {
            "title": app_name, "username": username, "password": password,
            "url": url, "notes": notes, "created_at": datetime.now().isoformat()
        }
        self._data['entries'].append(new_entry)
        self._append_log("CREATE", f"Entry added: {app_name}")
        self.save_vault()
        return True

    def delete_entry(self, index: int) -> bool:
        try:
            removed = self._data['entries'].pop(index)
            self._append_log("DELETE", f"Entry removed: {removed['title']}")
            self.save_vault()
            return True
        except IndexError:
            return False

    def update_entry(self, index: int, new_data: dict) -> bool:
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

    def add_entries_bulk(self, new_entries_data: list) -> bool:
        if not new_entries_data:
            return True
            
        original_state = copy.deepcopy(self._data)
        
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
            self._data = original_state
            raise RuntimeError(f"Bulk import failed, memory changes rolled back: {str(e)}")
        
    def verify_log_integrity(self) -> bool:
        """Verifies the cryptographic hash-chain integrity of the audit logs."""
        if not self._data or 'logs' not in self._data: 
            return True
        
        logs = self._data['logs']
        if not logs: 
            return True
            
        for i in range(len(logs) - 1):
            current_log = logs[i]
            prev_log = logs[i+1]
            
            if 'prev_hash' not in current_log:
                return False
            
            prev_log_str = json.dumps(prev_log, sort_keys=True).encode('utf-8')
            expected_hash = hashlib.sha256(prev_log_str).hexdigest()
            
            if current_log['prev_hash'] != expected_hash:
                return False
                
        if 'prev_hash' not in logs[-1] or logs[-1]['prev_hash'] != "0" * 64:
            return False
            
        return True