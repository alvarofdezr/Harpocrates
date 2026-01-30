import json
import os
from datetime import datetime
from core.crypto import HarpocratesCrypto

class VaultManager:
    def __init__(self, vault_path="vault.hpro"):
        self.vault_path = vault_path
        self.crypto = HarpocratesCrypto()

    def create_new_vault(self, master_password, secret_key):
        """Crea una nueva bóveda con soporte para logs."""
        empty_data = {
            "version": "1.4",
            "created_at": datetime.now().isoformat(),
            "entries": [],
            "logs": [] 
        }
        self._append_log(empty_data, "SYSTEM", "Vault Created")
        self.save_vault(empty_data, master_password, secret_key)

    def save_vault(self, data, master_password, secret_key):
        """Cifra y guarda los datos."""
        json_str = json.dumps(data)
        encrypted_data = self.crypto.encrypt_data(json_str, master_password, secret_key)
        
        with open(self.vault_path, 'wb') as f:
            f.write(encrypted_data)

    def load_vault(self, master_password, secret_key):
        """Carga, descifra y migra la estructura si es necesario."""
        if not os.path.exists(self.vault_path):
            raise FileNotFoundError("No se encuentra el archivo de la bóveda.")
            
        with open(self.vault_path, 'rb') as f:
            encrypted_data = f.read()
            
        decrypted_json = self.crypto.decrypt_data(encrypted_data, master_password, secret_key)
        data = json.loads(decrypted_json)

        if isinstance(data, list):
            data = {
                "version": "1.2 (Migrated)",
                "created_at": datetime.now().isoformat(),
                "entries": data,
                "logs": []
            }
        
        if 'logs' not in data:
            data['logs'] = []
            
        return data

    def _append_log(self, data, action, details):
        """Método interno para añadir log a un objeto data ya cargado."""
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action.upper(),
            "details": details
        }
        data['logs'].insert(0, log_entry)

    def add_audit_event(self, master_password, secret_key, action, details):
        """
        Método público para registrar eventos que no modifican datos 
        (ej: Login, Backup, Export).
        """
        data = self.load_vault(master_password, secret_key)
        self._append_log(data, action, details)
        self.save_vault(data, master_password, secret_key)

    def add_entry(self, master_password, secret_key, app_name, username, password, url="", notes=""):
        """Añade entrada y registra el evento automáticamente."""
        data = self.load_vault(master_password, secret_key)
        
        new_entry = {
            "title": app_name,
            "username": username,
            "password": password,
            "url": url,
            "notes": notes,
            "created_at": datetime.now().isoformat()
        }
        
        if 'entries' not in data: data['entries'] = []
        data['entries'].append(new_entry)
        
        self._append_log(data, "CREATE", f"Entry added: {app_name}")
        
        self.save_vault(data, master_password, secret_key)
        return True

    def delete_entry(self, master_password, secret_key, index):
        """Elimina entrada y registra el evento."""
        data = self.load_vault(master_password, secret_key)
        try:
            removed = data['entries'].pop(index)
            self._append_log(data, "DELETE", f"Entry removed: {removed['title']}")
            
            self.save_vault(data, master_password, secret_key)
            return True, f"Entrada '{removed['title']}' eliminada."
        except IndexError:
            return False, "Índice fuera de rango."

    def update_entry(self, master_password, secret_key, index, new_data):
        """Actualiza entrada y registra el evento."""
        data = self.load_vault(master_password, secret_key)
        try:
            entry = data['entries'][index]
            original_title = entry['title']
            
            if new_data.get('title'): entry['title'] = new_data['title']
            if new_data.get('username'): entry['username'] = new_data['username']
            if new_data.get('password'): entry['password'] = new_data['password']
            if new_data.get('url'): entry['url'] = new_data['url']
            if new_data.get('notes'): entry['notes'] = new_data['notes']
            
            entry['updated_at'] = datetime.now().isoformat()
            
            self._append_log(data, "UPDATE", f"Entry modified: {original_title}")
            
            self.save_vault(data, master_password, secret_key)
            return True, "Entrada actualizada correctamente."
        except IndexError:
            return False, "Índice no válido."