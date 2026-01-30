import os
import threading
import time
import shutil
import re
from datetime import datetime
from colorama import Fore, Style
import pyperclip
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
         ARCHITECTURE: Zero-Knowledge | ALGORITHMS: Argon2id + AES-256-GCM (v1.3)
    ---------------------------------------------------------------------------------------
"""

def secure_copy(data):
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
    score = 0
    if len(password) >= 12: score += 1
    if len(password) >= 16: score += 1
    if re.search(r"[A-Z]", password): score += 1
    if re.search(r"[a-z]", password): score += 1
    if re.search(r"\d", password): score += 1
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): score += 1
    
    if score < 3: return Fore.RED + "\n[!] ALERTA: Contraseña DÉBIL." + Style.RESET_ALL
    elif score < 5: return Fore.YELLOW + "\n[i] INFO: Contraseña DECENTE." + Style.RESET_ALL
    else: return Fore.GREEN + "\n[✓] EXCELENTE: Fortaleza criptográfica alta." + Style.RESET_ALL

def print_entry_details(entry):
    print("-" * 50)
    print(f"Servicio: {entry['title']}")
    print(f"Usuario:  {entry['username']}")
    print(f"URL:      {entry.get('url', 'N/A')}")
    if entry.get('notes'): print(Fore.YELLOW + f"Notas:    {entry['notes']}" + Style.RESET_ALL)
    print("-" * 50)

def entry_action_menu(vault, m_pass, s_key, entry, index):
    while True:
        print_entry_details(entry)
        print(f"\n[Acciones para: {Fore.CYAN}{entry['title']}{Style.RESET_ALL}]")
        print("1. Copiar Password")
        print("2. Editar Entrada")
        print("3. Eliminar Entrada")
        print("4. Volver")
        
        action = input("\nElige acción > ").strip()
        
        if action == '1':
            secure_copy(entry['password'])
            break
        elif action == '2':
            print(Fore.YELLOW + "\n--- MODO EDICIÓN ---" + Style.RESET_ALL)
            changes = {}
            val = input(f"Título [{entry['title']}]: "); changes['title'] = val if val else None
            val = input(f"Usuario [{entry['username']}]: "); changes['username'] = val if val else None
            val = input(f"Password [*******]: "); changes['password'] = val if val else None
            val = input(f"URL [{entry.get('url','')}] : "); changes['url'] = val if val else None
            val = input(f"Notas [{entry.get('notes','')}] : "); changes['notes'] = val if val else None
            
            clean_changes = {k: v for k, v in changes.items() if v is not None}
            
            if clean_changes:
                ok, msg = vault.update_entry(m_pass, s_key, index, clean_changes)
                print(f"\n{Fore.GREEN if ok else Fore.RED}[*] {msg}{Style.RESET_ALL}")
                break
            else: print("\n[i] Sin cambios.")

        elif action == '3':
            if input(Fore.RED + f"¿ELIMINAR '{entry['title']}'? (borrar): " + Style.RESET_ALL).lower() == 'borrar':
                ok, msg = vault.delete_entry(m_pass, s_key, index)
                print(f"\n{Fore.RED}[🗑️] {msg}{Style.RESET_ALL}")
                return True
        elif action == '4': break
    return False

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
        print(f"\n{'!'*60}\n  SECRET KEY: {s_key}\n  GUÁRDALA BIEN.\n{'!'*60}\n")
    else:
        s_key = input("[?] Secret Key: ")

    try:
        vault.load_vault(m_pass, s_key)
        vault.add_audit_event(m_pass, s_key, "LOGIN", "Access Granted via CLI")
        print(Fore.GREEN + "\n[✓] Acceso Concedido." + Style.RESET_ALL)
        
        while True:
            print(f"\n{'-'*30} MENÚ PRINCIPAL (v1.3) {'-'*30}")
            print("1. [L] Listar    2. [A] Añadir    3. [B] Buscar")
            print("4. [G] Generar   5. [I] Importar  6. [S] Salir")
            print("7. [K] Backup    8. [LOG] Ver Auditoría") 
            
            opcion = input("\nHarpocrates > ").lower().strip()

            if opcion in ['1', 'l']:
                data = vault.load_vault(m_pass, s_key)
                entries = data.get('entries', [])
                if not entries: print("[!] Vacío.")
                else:
                    print(f"\n{'ID':<4} | {'SERVICIO':<20} | {'USUARIO':<20}")
                    print("-" * 50)
                    for idx, e in enumerate(entries):
                        print(f"{idx:<4} | {e['title']:<20} | {e['username']:<20}")
                    sel = input("\n[?] ID para Gestionar (Enter volver): ")
                    if sel.isdigit() and int(sel) < len(entries):
                        entry_action_menu(vault, m_pass, s_key, entries[int(sel)], int(sel))

            elif opcion in ['2', 'a']:
                t = input("Servicio: ")
                u = input("Usuario: ")
                pw = PasswordGenerator.generate(24) if input("¿Generar pass? (s/n): ")=='s' else input("Password: ")
                if len(pw)>0: print(check_strength(pw))
                url = input("URL: ")
                n = input("Notas: ")
                vault.add_entry(m_pass, s_key, t, u, pw, url, n)
                print(Fore.GREEN + "[✓] Guardado." + Style.RESET_ALL)

            elif opcion in ['3', 'b']:
                q = input("Buscar: ").lower()
                data = vault.load_vault(m_pass, s_key)
                res = [(i, e) for i, e in enumerate(data['entries']) if q in e['title'].lower() or q in e['username'].lower()]
                if not res: print("[!] Sin resultados.")
                else:
                    for i, (oidx, e) in enumerate(res): print(f"[{i}] {e['title']}")
                    sel = input("Selección: ")
                    if sel.isdigit() and int(sel) < len(res):
                        entry_action_menu(vault, m_pass, s_key, res[int(sel)][1], res[int(sel)][0])

            elif opcion in ['4', 'g']:
                p = PasswordGenerator.generate(32)
                print(f"\n[+] {Fore.GREEN}{p}{Style.RESET_ALL}")
                if input("¿Copiar? (s/n): ")=='s': secure_copy(p)

            elif opcion in ['5', 'i']:
                path = input("CSV: ").strip().strip('"')
                if os.path.exists(path) and input("¿Importar? (s/n): ")=='s':
                    qty, msg = import_from_csv(path, vault, s_key, m_pass)
                    if qty > 0:
                        vault.add_audit_event(m_pass, s_key, "IMPORT", f"Imported {qty} items from CSV")
                        print(Fore.GREEN + msg + Style.RESET_ALL)
                        if input("¿Borrar CSV? (s/n): ")=='s': os.remove(path)
                    else: print(Fore.RED + msg + Style.RESET_ALL)

            elif opcion in ['6', 's']: break

            elif opcion in ['7', 'k']:
                if os.path.exists(vault_path):
                    bk_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.hpro"
                    shutil.copy(vault_path, bk_name)
                    vault.add_audit_event(m_pass, s_key, "BACKUP", f"Created: {bk_name}")
                    print(Fore.GREEN + f"[✓] Backup: {bk_name}" + Style.RESET_ALL)

            # --- NUEVA OPCIÓN: AUDIT LOG ---
            elif opcion in ['8', 'log', 'audit']:
                data = vault.load_vault(m_pass, s_key)
                logs = data.get('logs', [])
                print(Fore.CYAN + f"\n=== REGISTRO DE SUCESOS ({len(logs)}) ===" + Style.RESET_ALL)
                print(f"{'FECHA':<20} | {'ACCIÓN':<10} | {'DETALLE'}")
                print("-" * 60)
                for log in logs[:15]:
                    print(f"{log['timestamp']:<20} | {log['action']:<10} | {log['details']}")
                if len(logs) > 15:
                    print(f"... y {len(logs)-15} eventos más antiguos.")
                input("\nPresiona Enter para volver...")

    except Exception as e:
        # Penalización por fuerza bruta (Rate Limiting)
        print(Fore.RED + f"\n[X] Autenticación Fallida." + Style.RESET_ALL)
        print(Fore.YELLOW + "[!] Aplicando protocolo de seguridad contra fuerza bruta..." + Style.RESET_ALL)
    
        time.sleep(3) 
        
        print(f"[debug] Error técnico: {e}")
        print("[!] La aplicación se cerrará.")

if __name__ == "__main__":
    pass