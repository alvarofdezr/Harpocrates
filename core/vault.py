import json
import os
from datetime import datetime
from core.crypto import HarpocratesCrypto

class VaultManager:
    def __init__(self, vault_path="vault.hpro"):
        self.vault_path = vault_path
        self.crypto = HarpocratesCrypto()

    def create_new_vault(self, master_password, secret_key):
        """Crea una nueva bóveda vacía con estructura v1.2."""
        empty_data = {
            "version": "1.2",
            "created_at": datetime.now().isoformat(),
            "entries": []
        }
        self.save_vault(empty_data, master_password, secret_key)

    def save_vault(self, data, master_password, secret_key):
        """Cifra y guarda el diccionario de datos."""
        json_str = json.dumps(data)
        encrypted_data = self.crypto.encrypt_data(json_str, master_password, secret_key)
        
        with open(self.vault_path, 'wb') as f:
            f.write(encrypted_data)

    def load_vault(self, master_password, secret_key):
        """
        Lee y descifra la bóveda.
        INCLUYE MIGRACIÓN AUTOMÁTICA: Si detecta formato antiguo (lista), lo convierte a diccionario.
        """
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
                "entries": data 
            }
        
        return data

    def add_entry(self, master_password, secret_key, app_name, username, password, url="", notes=""):
        """Añade una entrada asegurándose de usar la estructura de diccionario."""
        data = self.load_vault(master_password, secret_key)
        new_entry = {
            "title": app_name,
            "username": username,
            "password": password,
            "url": url,
            "notes": notes,
            "created_at": datetime.now().isoformat()
        }
        if 'entries' not in data:
            data['entries'] = []
            
        data['entries'].append(new_entry)
        
        self.save_vault(data, master_password, secret_key)
        return True