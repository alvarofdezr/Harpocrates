import json
import os
import uuid
from datetime import datetime
from core.crypto import HarpocratesCrypto

class VaultManager:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.crypto = HarpocratesCrypto()

    def create_new_vault(self, master_password: str, secret_key: str):
        """Inicializa una bóveda vacía con una nueva clave maestra y secret key."""
        salt = os.urandom(16)
        initial_data = {
            "version": "1.0", 
            "entries": []
        }
        
        key = self.crypto.derive_key(master_password, secret_key, salt)
        serialized_data = json.dumps(initial_data).encode('utf-8')
        encrypted_payload = self.crypto.encrypt(serialized_data, key)
        
        with open(self.file_path, 'wb') as f:
            f.write(salt)
            f.write(encrypted_payload)

    def load_vault(self, master_password: str, secret_key: str) -> dict:
        """Lee y descifra la bóveda usando ambos factores."""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError("La bóveda no existe.")

        with open(self.file_path, 'rb') as f:
            salt = f.read(16)
            encrypted_payload = f.read()

        key = self.crypto.derive_key(master_password, secret_key, salt)
        
        try:
            decrypted_data = self.crypto.decrypt(encrypted_payload, key)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception:
            raise ValueError("Autenticación fallida: Contraseña o Secret Key incorrectos.")

    def save_vault(self, master_password: str, data: dict):
        """Actualiza el contenido de la bóveda."""
        self.create_new_vault(master_password) 

    def add_entry(self, master_password: str, secret_key: str, title: str, username: str, password_str: str, url: str = ""):
        """Añade una entrada, cifra y sobreescribe la bóveda de forma segura."""
        data = self.load_vault(master_password, secret_key)
        
        new_entry = {
            "id": str(uuid.uuid4()),
            "title": title,
            "username": username,
            "password": password_str,
            "url": url,
            "created_at": datetime.now().isoformat()
        }
        
        data["entries"].append(new_entry)
        
        self._save_and_rotate(master_password, secret_key, data)

    def _save_and_rotate(self, master_password: str, secret_key: str, data: dict):
        """Privado: Procesa el cifrado y guardado físico."""
        salt = os.urandom(16)
        serialized_data = json.dumps(data).encode('utf-8')
        key = self.crypto.derive_key(master_password, secret_key, salt)
        encrypted_payload = self.crypto.encrypt(serialized_data, key)
        
        with open(self.file_path, 'wb') as f:
            f.write(salt)
            f.write(encrypted_payload)
