import json
import os
from datetime import datetime
from core.crypto import HarpocratesCrypto

class VaultManager:
    def __init__(self, vault_path="vault.hpro"):
        self.vault_path = vault_path
        self.crypto = HarpocratesCrypto()

    def create_new_vault(self, master_password, secret_key):
        """Crea bóveda v1.5 con soporte para Logs."""
        empty_data = {
            "version": "1.5",
            "created_at": datetime.now().isoformat(),
            "entries": [],
            "logs": [] 
        }
        self._append_log(empty_data, "SYSTEM", "Vault Created")
        self.save_vault(empty_data, master_password, secret_key)

    def save_vault(self, data, master_password, secret_key):
        json_str = json.dumps(data)
        encrypted_data = self.crypto.encrypt_data(json_str, master_password, secret_key)
        with open(self.vault_path, 'wb') as f:
            f.write(encrypted_data)

    def load_vault(self, master_password, secret_key):
        if not os.path.exists(self.vault_path):
            raise FileNotFoundError("No se encuentra el archivo.")
            
        with open(self.vault_path, 'rb') as f:
            encrypted_data = f.read()
            
        decrypted_json = self.crypto.decrypt_data(encrypted_data, master_password, secret_key)
        data = json.loads(decrypted_json)

        # --- MIGRACIÓN AUTOMÁTICA v1.4 -> v1.5 ---
        if isinstance(data, dict) and data.get("version") == "1.4":
            data['version'] = "1.5"
            self._append_log(data, "SYSTEM", "Upgraded to v1.5 (Enhanced Security)")
            self.save_vault(data, master_password, secret_key)
            
        return data

    def _append_log(self, data, action, details):
        """Escribe en el log interno (privado)."""
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action.upper(),
            "details": details
        }

        if 'logs' not in data: data['logs'] = []
        data['logs'].insert(0, log_entry)

    def add_audit_event(self, master_password, secret_key, action, details):
        """Registra eventos externos (Login, Backup, HIBP Scan)."""
        data = self.load_vault(master_password, secret_key)
        self._append_log(data, action, details)
        self.save_vault(data, master_password, secret_key)

    def add_entry(self, master_password, secret_key, app_name, username, password, url="", notes=""):
        data = self.load_vault(master_password, secret_key)
        new_entry = {
            "title": app_name, "username": username, "password": password,
            "url": url, "notes": notes, "created_at": datetime.now().isoformat()
        }
        if 'entries' not in data: data['entries'] = []
        data['entries'].append(new_entry)
        
        self._append_log(data, "CREATE", f"Entry added: {app_name}")
        
        self.save_vault(data, master_password, secret_key)
        return True

    def delete_entry(self, master_password, secret_key, index):
        data = self.load_vault(master_password, secret_key)
        try:
            removed = data['entries'].pop(index)
            self._append_log(data, "DELETE", f"Entry removed: {removed['title']}")
            self.save_vault(data, master_password, secret_key)
            return True, f"Eliminado: {removed['title']}"
        except IndexError:
            return False, "Índice error."

    def update_entry(self, master_password, secret_key, index, new_data):
        data = self.load_vault(master_password, secret_key)
        try:
            entry = data['entries'][index]
            original_title = entry['title']
            
            for k, v in new_data.items():
                if v: entry[k] = v
            
            entry['updated_at'] = datetime.now().isoformat()

            self._append_log(data, "UPDATE", f"Modified: {original_title}")
            
            self.save_vault(data, master_password, secret_key)
            return True, "Actualizado."
        except IndexError:
            return False, "Error."