import os
import threading
import time
import re
import pyperclip
from colorama import Fore, Style
from dotenv import load_dotenv
from core.vault import VaultManager
from core.crypto import HarpocratesCrypto
from core.generator import PasswordGenerator
from core.importer import import_from_csv

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
         ARCHITECTURE: Zero-Knowledge | ALGORITHMS: Argon2id + AES-256-GCM (v1.2)
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

def check_strength(password):
    """Analiza la fortaleza de la contraseña y devuelve un feedback visual."""
    score = 0
    if len(password) >= 12: score += 1
    if len(password) >= 16: score += 1
    if re.search(r"[A-Z]", password): score += 1
    if re.search(r"[a-z]", password): score += 1
    if re.search(r"\d", password): score += 1
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): score += 1
    
    if score < 3:
        return Fore.RED + "\n[!] ALERTA: Contraseña DÉBIL. Se recomienda usar el generador." + Style.RESET_ALL
    elif score < 5:
        return Fore.YELLOW + "\n[i] INFO: Contraseña DECENTE, pero podría mejorar." + Style.RESET_ALL
    else:
        return Fore.GREEN + "\n[✓] EXCELENTE: Fortaleza criptográfica alta." + Style.RESET_ALL

def print_entry_details(entry):
    """Muestra los detalles completos de una entrada, incluyendo notas."""
    print("-" * 40)
    print(f"Servicio: {entry['title']}")
    print(f"Usuario:  {entry['username']}")
    print(f"URL:      {entry.get('url', 'N/A')}")
    
    if entry.get('notes'):
        print(Fore.YELLOW + f"Notas:    {entry['notes']}" + Style.RESET_ALL)
    print("-" * 40)

def run_cli():
    os.system('cls' if os.name == 'nt' else 'clear')  # nosec
    print(BANNER)
    
    crypto = HarpocratesCrypto()
    vault_path = os.getenv("VAULT_PATH", "vault.hpro")
    vault = VaultManager(vault_path)

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
        vault.load_vault(m_pass, s_key)
        print(Fore.GREEN + "\n[✓] Acceso Concedido. Bóveda descifrada en memoria." + Style.RESET_ALL)
        
        while True:
            print(f"\n{'-'*30} MENÚ PRINCIPAL {'-'*30}")
            print("1. [L] Listar")
            print("2. [A] Añadir Entrada")
            print("3. [B] Buscar")
            print("4. [G] Generar Password")
            print("5. [I] Importar CSV (Bitwarden/Chrome)")
            print("6. [S] Salir")
            
            opcion = input("\nHarpocrates > ").lower().strip()

            # --- OPCIÓN 1: LISTAR ---
            if opcion in ['1', 'l', 'listar']:
                data = vault.load_vault(m_pass, s_key)
                entries = data.get('entries', [])
                if not entries:
                    print("[!] La bóveda está vacía.")
                else:
                    print(f"\n{'ID':<4} | {'SERVICIO':<25} | {'USUARIO':<25}")
                    print("-" * 60)
                    for idx, e in enumerate(entries):
                        print(f"{idx:<4} | {e['title']:<25} | {e['username']:<25}")
                    
                    sel = input("\n[?] Introduce ID para ver detalles y copiar pass (o Enter para volver): ")
                    if sel.isdigit() and int(sel) < len(entries):
                        selected = entries[int(sel)]
                        print_entry_details(selected) 
                        secure_copy(selected['password'])

            # --- OPCIÓN 2: AÑADIR ---
            elif opcion in ['2', 'a', 'añadir']:
                print(Fore.CYAN + "\n--- Nueva Entrada ---" + Style.RESET_ALL)
                title = input("Servicio: ")
                user = input("Usuario/Email: ")
                url = input("URL (opcional): ")
                notes = input("Notas (opcional): ") 
                
                if input("¿Generar password aleatorio? (s/n): ").lower() == 's':
                    pw = PasswordGenerator.generate(24)
                    print(f"[+] Password generado: {Fore.GREEN}{pw}{Style.RESET_ALL}")
                else:
                    pw = input("Password: ")
                    print(check_strength(pw))
                    
                vault.add_entry(m_pass, s_key, title, user, pw, url, notes)
                print(Fore.GREEN + "[✓] Entrada cifrada y guardada correctamente." + Style.RESET_ALL)

            # --- OPCIÓN 3: BUSCAR ---
            elif opcion in ['3', 'b', 'buscar']:
                query = input("[?] Término de búsqueda: ").lower()
                data = vault.load_vault(m_pass, s_key)
                results = []
                for idx, e in enumerate(data['entries']):
                    if query in e['title'].lower() or query in e['username'].lower():
                        results.append((idx, e))
                
                if not results:
                    print("[!] No hay coincidencias.")
                else:
                    print(f"\nResultados encontrados: {len(results)}")
                    for i, (original_idx, e) in enumerate(results):
                        print(f"[{i}] {e['title']} ({e['username']})")
                    
                    sel = input("\n[?] Selecciona el número de la lista (o Enter): ")
                    if sel.isdigit() and int(sel) < len(results):
                        _, selected_entry = results[int(sel)]
                        print_entry_details(selected_entry) 
                        secure_copy(selected_entry['password'])

            # --- OPCIÓN 4: GENERAR ---
            elif opcion in ['4', 'g', 'generar']:
                gen_pw = PasswordGenerator.generate(32)
                print(f"\n[+] Sugerencia segura: {Fore.GREEN}{gen_pw}{Style.RESET_ALL}")
                if input("¿Copiar al portapapeles? (s/n): ").lower() == 's':
                    secure_copy(gen_pw)
            
            # --- OPCIÓN 5: IMPORTAR CSV ---
            elif opcion in ['5', 'i', 'importar']:
                print(Fore.YELLOW + "\n[!] ADVERTENCIA: Soporta formato Bitwarden/Chrome." + Style.RESET_ALL)
                csv_path = input("Ruta del archivo CSV (arrastra el archivo aquí): ").strip().strip('"')

                if os.path.exists(csv_path):
                    confirm = input(f"¿Importar desde '{csv_path}'? (s/n): ")
                    if confirm.lower() == 's':
                        qty, msg = import_from_csv(csv_path, vault, s_key, m_pass)

                        if qty > 0:
                            print(Fore.GREEN + f"\n{msg}" + Style.RESET_ALL)
                            del_csv = input(Fore.RED + "¿Borrar CSV original por seguridad? (s/n): " + Style.RESET_ALL)
                            if del_csv.lower() == 's':
                                os.remove(csv_path)
                                print("[✓] Archivo eliminado.")
                        else:
                            print(Fore.RED + f"\n[X] {msg}" + Style.RESET_ALL)
                else:
                    print(Fore.RED + "[!] El archivo no existe." + Style.RESET_ALL)

            # --- OPCIÓN 6: SALIR ---
            elif opcion in ['6', 's', 'salir', 'exit']:
                print("\n[i] Cerrando sesión y limpiando memoria...")
                break

    except Exception as e:
        print(Fore.RED + f"\n[X] Error Crítico / Autenticación Fallida: {e}" + Style.RESET_ALL)
        print("[!] La aplicación se cerrará.")

if __name__ == "__main__":
    pass