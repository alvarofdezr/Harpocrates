import json
import os
import copy
import hashlib
import hmac
from datetime import datetime
from core.crypto import HarpocratesCrypto
from core.exceptions import HarpocratesError, VaultNotFoundError, VaultCorruptError, VaultMigrationRequired

VERSION = "2.0.0"
VAULT_FORMAT = 2

class VaultManager:
    def __init__(self, vault_path: str = "vault.hpro") -> None:
        self.vault_path = os.path.abspath(vault_path)
        self.crypto = HarpocratesCrypto()
        self._data = None
        self._session_key = None
        self._salt = None

    def create_new_vault(self, master_password: str, secret_key: str) -> None:
        """Initializes a new vault with the latest schema and a signed genesis log."""
        self._salt = os.urandom(self.crypto.salt_size)
        self._session_key = self.crypto.derive_session_key(master_password, secret_key, self._salt)
        self._data = {
            "vault_format": VAULT_FORMAT, 
            "app_version": VERSION, 
            "entries": [], 
            "logs": []
        }
        self._append_log("SYSTEM", "Vault Created")
        self._update_genesis_hmac()
        self.save_vault()

    def _update_genesis_hmac(self) -> None:
        """Calculates and stores the HMAC for the genesis block (the oldest log)."""
        if not self._data or not self._data.get('logs'):
            return
        genesis_log = self._data['logs'][-1]
        message = json.dumps(genesis_log, sort_keys=True).encode('utf-8')
        mac = hmac.HMAC(self._session_key, message, hashlib.sha256)
        self._data['log_genesis_hmac'] = mac.hexdigest()

    def load_vault(self, master_password: str, secret_key: str) -> bool:
        if not os.path.exists(self.vault_path):
            raise VaultNotFoundError(f"Vault file not found: {self.vault_path}")
            
        with open(self.vault_path, 'rb') as f:
            encrypted_data = f.read()
            
        salt = encrypted_data[:self.crypto.salt_size]
        session_key = self.crypto.derive_session_key(master_password, secret_key, salt)
        
        decrypted_json = self.crypto.decrypt_with_session_key(encrypted_data, session_key, salt)
        data = json.loads(decrypted_json)
        
        fmt = data.get('vault_format', 1)
        
        if fmt > VAULT_FORMAT:
            raise VaultCorruptError("Vault format is newer than this application version.")
        
        if fmt == 1:
            self._pending_migration_data = data
            self._pending_migration_key = session_key
            self._pending_migration_salt = salt
            raise VaultMigrationRequired("Vault is v1 format. Migration required.")
        
        self._salt = salt
        self._session_key = session_key
        self._data = data
        return True

    def migrate_to_v2(self) -> None:
        """Upgrades an already decrypted v1 vault to the v2 schema with a signed genesis block."""
        if not hasattr(self, '_pending_migration_data'):
            raise HarpocratesError("There is no pending migration data. Load a v1 vault first.")
        
        data = self._pending_migration_data
        data['vault_format'] = VAULT_FORMAT
        data['app_version'] = VERSION
        data.pop('version', None)
        
        # Promover al estado oficial
        self._salt = self._pending_migration_salt
        self._session_key = self._pending_migration_key
        self._data = data
        
        self._update_genesis_hmac()
        self.save_vault()
        
        # Limpiar estado temporal
        del self._pending_migration_data
        del self._pending_migration_key
        del self._pending_migration_salt

    def save_vault(self) -> None:
        if self._data is None or self._session_key is None:
            return
            
        json_str = json.dumps(self._data)
        encrypted_data = self.crypto.encrypt_with_session_key(json_str, self._session_key, self._salt)
        
        tmp_path = self.vault_path + ".tmp"
        try:
            fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, 'wb') as f:
                f.write(encrypted_data)
                f.flush()
                os.fsync(f.fileno())
                
            os.replace(tmp_path, self.vault_path)
            
            if os.name == 'posix':
                os.chmod(self.vault_path, 0o600)
                
        except OSError:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    def get_entries(self) -> list:
        """Returns a deep copy to prevent external mutation of internal state."""
        return copy.deepcopy(self._data.get('entries', []))

    def get_logs(self) -> list:
        """Returns a deep copy of the audit logs."""
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
        """Atomically imports multiple entries, rolling back on failure."""
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
        if not self._data or 'logs' not in self._data:
            return True
        
        logs = self._data['logs']
        if not logs:
            return True
        
        MAX_VERIFY = 10_000
        logs_to_check = logs[:MAX_VERIFY]
        
        for i in range(len(logs_to_check) - 1):
            current_log = logs_to_check[i]
            prev_log = logs_to_check[i + 1]
            
            if 'prev_hash' not in current_log or not isinstance(current_log['prev_hash'], str):
                return False
            
            prev_log_str = json.dumps(prev_log, sort_keys=True).encode('utf-8')
            expected_hash = hashlib.sha256(prev_log_str).hexdigest()
            
            if not hmac.compare_digest(current_log['prev_hash'], expected_hash):  # timing-safe
                return False
        
        genesis = logs[-1]
        if 'prev_hash' not in genesis or not isinstance(genesis['prev_hash'], str):
            return False
        if not hmac.compare_digest(genesis['prev_hash'], "0" * 64):
            return False

        expected_hmac = self._data.get('log_genesis_hmac')
        if not expected_hmac:
            return False
            
        message = json.dumps(genesis, sort_keys=True).encode('utf-8')
        mac = hmac.HMAC(self._session_key, message, hashlib.sha256)
        calculated_hmac = mac.hexdigest()
        
        return hmac.compare_digest(calculated_hmac, expected_hmac)