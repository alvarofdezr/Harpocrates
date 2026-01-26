import os
import threading
import time
import pyperclip
from dotenv import load_dotenv
from core.vault import VaultManager
from core.crypto import HarpocratesCrypto
from core.generator import PasswordGenerator

# Cargar configuración desde .env
load_dotenv()

BANNER = r"""
 ██╗  ██╗ █████╗ ██████╗ ██████╗  ██████╗  ██████╗██████╗  █████╗ ████████╗███████╗███████╗
 ██║  ██║██╔══██╗██╔══██╗██╔══██╗██╔═══██╗██╔════╝██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██╔════╝
 ███████║███████║██████╔╝██████╔╝██║   ██║██║     ██████╔╝███████║   ██║   █████╗  ███████╗
 ██╔══██║██╔══██║██╔══██╗██╔═══╝ ██║   ██║██║     ██╔══██╗██╔══██║   ██║   ██╔══╝  ╚════██║
 ██║  ██║██║  ██║██║  ██║██║     ╚██████╔╝╚██████╗██║  ██║██║  ██║   ██║   ███████╗███████║
 ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝      ╚═════╝  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚══════╝
                                 [ SILENCE IS SECURITY ]
    ---------------------------------------------------------------------------------------
         ARCHITECTURE: Zero-Knowledge | ALGORITHMS: Argon2id + AES-256-GCM (v1.0)
    ---------------------------------------------------------------------------------------
"""

def secure_copy(data):
    """Copia al portapapeles y limpia tras 20 segundos en un hilo independiente."""
    try:
        pyperclip.copy(data)
        print(f"\n[i] Portapapeles: Datos copiados. Se borrarán automáticamente en 20s.")
        
        def clear():
            time.sleep(20)
            if pyperclip.paste() == data:
                pyperclip.copy("")
                print("\n[i] Portapapeles limpiado por seguridad.")
        
        threading.Thread(target=clear, daemon=True).start()
    except Exception as e:
        print(f"[!] Error al acceder al portapapeles: {e}")

def run_cli():
    # Limpiar pantalla según SO
    os.system('cls' if os.name == 'nt' else 'clear')
    print(BANNER)
    
    crypto = HarpocratesCrypto()
    vault_path = os.getenv("VAULT_PATH", "vault.hpro")
    vault = VaultManager(vault_path)

    # Autenticación inicial
    m_pass = input("[?] Master Password: ")
    
    if not os.path.exists(vault_path):
        print("\n[!] Bóveda no detectada. Generando nueva instancia...")
        s_key = crypto.generate_secret_key()
        vault.create_new_vault(m_pass, s_key)
        print(f"\n{'!'*60}")
        print(f"  TU SECRET KEY ES: {s_key}")
        print("  GUÁRDALA EN UN LUGAR FÍSICO. SIN ELLA NO PODRÁS RECUPERAR NADA.")
        print(f"{'!'*60}\n")
    else:
        s_key = input("[?] Secret Key: ")

    try:
        # Validación de integridad inicial
        vault.load_vault(m_pass, s_key)
        print("\n[✓] Acceso Concedido. Bóveda descifrada en memoria.")
        
        while True:
            print(f"\n{'-'*30} MENÚ PRINCIPAL {'-'*30}")
            print("1. [L] Listar | 2. [A] Añadir | 3. [B] Buscar | 4. [G] Generar | 5. [S] Salir")
            opcion = input("\nHarpocrates > ").lower().strip()

            if opcion in ['1', 'l', 'listar']:
                data = vault.load_vault(m_pass, s_key)
                entries = data.get('entries', [])
                if not entries:
                    print("[!] La bóveda está vacía.")
                else:
                    print(f"\n{'ID':<4} | {'SERVICIO':<20} | {'USUARIO':<20}")
                    print("-" * 50)
                    for idx, e in enumerate(entries):
                        print(f"{idx:<4} | {e['title']:<20} | {e['username']:<20}")
                    
                    sel = input("\n[?] Introduce ID para copiar password (o Enter para volver): ")
                    if sel.isdigit() and int(sel) < len(entries):
                        secure_copy(entries[int(sel)]['password'])

            elif opcion in ['2', 'a', 'añadir']:
                title = input("Servicio: ")
                user = input("Usuario/Email: ")
                url = input("URL: ")
                if input("¿Generar password aleatorio? (s/n): ").lower() == 's':
                    pw = PasswordGenerator.generate(24)
                    print(f"[+] Password generado: {pw}")
                else:
                    pw = input("Password: ")
                
                vault.add_entry(m_pass, s_key, title, user, pw, url)
                print("[✓] Entrada cifrada y guardada correctamente.")

            elif opcion in ['3', 'b', 'buscar']:
                query = input("[?] Término de búsqueda: ").lower()
                data = vault.load_vault(m_pass, s_key)
                results = [e for e in data['entries'] if query in e['title'].lower() or query in e['username'].lower()]
                
                if not results:
                    print("[!] No hay coincidencias.")
                else:
                    for idx, e in enumerate(results):
                        print(f"{idx} | {e['title']} | {e['username']}")
                    sel = input("\n[?] ID para copiar password: ")
                    if sel.isdigit() and int(sel) < len(results):
                        secure_copy(results[int(sel)]['password'])

            elif opcion in ['4', 'g', 'generar']:
                print(f"\n[+] Sugerencia segura: {PasswordGenerator.generate(32)}")

            elif opcion in ['5', 's', 'salir', 'exit']:
                break

    except Exception as e:
        print(f"\n[X] Error de Autenticación: {e}")
        print("[!] Por seguridad, la aplicación se cerrará.")