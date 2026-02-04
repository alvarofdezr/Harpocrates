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
from core.auditor import PasswordAuditor  
from core.osint import OsintScanner 
load_dotenv()

BANNER = r"""
    ██╗  ██╗ █████╗ ██████╗ ██████╗  ██████╗  ██████╗██████╗  █████╗ ████████╗███████╗███████╗
    ██║  ██║██╔══██╗██╔══██╗██╔══██╗██╔═══██╗██╔════╝██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██╔════╝
    ███████║███████║██████╔╝██████╔╝██║   ██║██║     ██████╔╝███████║   ██║   █████╗  ███████╗
    ██╔══██║██╔══██║██╔══██╗██╔═══╝ ██║   ██║██║     ██╔══██╗██╔══██║   ██║   ██╔══╝  ╚════██║
    ██║  ██║██║  ██║██║  ██║██║     ╚██████╔╝╚██████╗██║  ██║██║  ██║   ██║   ███████╗███████║
    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝      ╚═════╝  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚══════╝
                                    [ SILENCE IS SECURITY ]
    ------------------------------------------------------------------------------------------
            ARCHITECTURE: Zero-Knowledge | ALGORITHMS: Argon2id + AES-256-GCM (v1.5.0)
    ------------------------------------------------------------------------------------------
"""

def secure_copy(data):
    try:
        pyperclip.copy(data)
        print(f"\n[i] Portapapeles: Datos copiados. Se borrarán en 20s.")
        def clear():
            time.sleep(20)
            if pyperclip.paste() == data:
                pyperclip.copy("")
        threading.Thread(target=clear, daemon=True).start()
    except Exception:
        print(Fore.YELLOW + "[!] No se pudo acceder al portapapeles." + Style.RESET_ALL)

def check_strength(pw):
    s=0
    if len(pw)>=12: s+=1
    if re.search(r"\d", pw): s+=1
    if re.search(r"[A-Z]", pw): s+=1
    if re.search(r"[!@#$%^&*]", pw): s+=1
    if s<3: return Fore.RED + "DÉBIL" + Style.RESET_ALL
    return Fore.GREEN + "FUERTE" + Style.RESET_ALL

def entry_action_menu(vault, m_pass, s_key, entry, index):
    """Submenú de gestión v1.5.0"""
    while True:
        print(f"\nServicio: {Fore.CYAN}{entry['title']}{Style.RESET_ALL} | User: {entry['username']}")
        if entry.get('notes'): print(f"Notas: {Fore.YELLOW}{entry['notes']}{Style.RESET_ALL}")
        
        print("\n1. Copiar Pass  2. Editar  3. Borrar  4. Volver")
        op = input("> ")
        
        if op == '1':
            secure_copy(entry['password'])
            break
        elif op == '2':
            print("--- Deja vacío para no cambiar ---")
            chg = {}
            for field in ['title','username','password','url','notes']:
                val = input(f"{field.capitalize()}: ")
                if val: chg[field] = val
            if chg:
                vault.update_entry(m_pass, s_key, index, chg)
                print(Fore.GREEN + "[✓] Actualizado." + Style.RESET_ALL)
                break
        elif op == '3':
            if input("¿Borrar? (s/n): ") == 's':
                vault.delete_entry(m_pass, s_key, index)
                print(Fore.RED + "[✓] Eliminado." + Style.RESET_ALL)
                return True
        elif op == '4': break
    return False

def run_cli():
    os.system('cls' if os.name == 'nt' else 'clear') # nosec
    print(BANNER)
    
    vault = VaultManager()
    crypto = HarpocratesCrypto()
    
    if not os.path.exists("vault.hpro"):
        m_pass = input("Crea tu Master Password: ")
        s_key = crypto.generate_secret_key()
        vault.create_new_vault(m_pass, s_key)
        print(f"\nSECRET KEY: {s_key}\n¡GUÁRDALA!")
    
    m_pass = input("[?] Master Password: ")
    s_key = input("[?] Secret Key: ")
    
    try:
        vault.load_vault(m_pass, s_key)
        vault.add_audit_event(m_pass, s_key, "LOGIN", "Access via CLI")
        print(Fore.GREEN + "\n[✓] Acceso Concedido." + Style.RESET_ALL)
        
        while True:
            print(f"\n{'-'*30} MENÚ v1.5.0 {'-'*40}")
            print("1.  Listar       2. Añadir      3. Buscar")
            print("4.  Generar      5. Importar    6. Salir")
            print("7.  Backup       8. Ver Logs    9. Escáner HIBP")
            print("10. OSINT Identity Tracer")
            op = input("\n> ").strip()
            
            if op == '1':
                data = vault.load_vault(m_pass, s_key)
                entries = data.get('entries', [])
                print(f"\nID    | {'SERVICIO':<40} | USUARIO")
                print("-" * 60)
                for i, e in enumerate(entries):
                    print(f"{i:<4} | {e['title']:<40} | {e['username']}")
                sel = input("\nID para gestionar (Enter volver): ")
                if sel.isdigit() and int(sel) < len(entries):
                    entry_action_menu(vault, m_pass, s_key, entries[int(sel)], int(sel))

            elif op == '2':
                t = input("Servicio: ")
                u = input("Usuario: ")
                p = PasswordGenerator.generate(24) if input("¿Auto-pass? (s/n): ")=='s' else input("Pass: ")
                print(check_strength(p))
                vault.add_entry(m_pass, s_key, t, u, p, input("URL: "), input("Notas: "))
                print("[✓] Guardado.")

            elif op == '3':
                q = input("Buscar: ").lower()
                data = vault.load_vault(m_pass, s_key)
                res = [(i,e) for i,e in enumerate(data['entries']) if q in e['title'].lower()]
                for i, (idx, e) in enumerate(res): print(f"[{i}] {e['title']}")
                if res:
                    sel = input("Selección: ")
                    if sel.isdigit() and int(sel) < len(res):
                        entry_action_menu(vault, m_pass, s_key, res[int(sel)][1], res[int(sel)][0])

            elif op == '4':
                pw = PasswordGenerator.generate(32)
                print(f"Pass: {Fore.GREEN}{pw}{Style.RESET_ALL}")
                if input("¿Copiar? (s/n): ")=='s': secure_copy(pw)

            elif op == '5':
                path = input("CSV: ").strip('"')
                if input("¿Importar? (s/n): ")=='s':
                    qty, msg = import_from_csv(path, vault, s_key, m_pass)
                    print(msg)
                    if qty > 0: vault.add_audit_event(m_pass, s_key, "IMPORT", f"Imported {qty} items")

            elif op == '6': break

            elif op == '7':
                bk = f"backup_{datetime.now().strftime('%Y%m%d_%H%M')}.hpro"
                shutil.copy("vault.hpro", bk)
                vault.add_audit_event(m_pass, s_key, "BACKUP", f"Created {bk}")
                print(f"[✓] Backup: {bk}")

            elif op == '8':
                data = vault.load_vault(m_pass, s_key)
                logs = data.get('logs', [])
                print(Fore.CYAN + f"\n--- REGISTRO FORENSE ({len(logs)}) ---" + Style.RESET_ALL)
                for l in logs[:15]: 
                    print(f"{l['timestamp']} | {l['action']:<10} | {l['details']}")
                input("\nEnter para volver...")

            elif op == '9':
                print(Fore.YELLOW + "\n[!] Conectando con HaveIBeenPwned (K-Anonymity)..." + Style.RESET_ALL)
                data = vault.load_vault(m_pass, s_key)
                bad_count = 0
                
                for e in data['entries']:
                    print(f"[*] Analizando {e['title']}...", end="", flush=True)
                    c = PasswordAuditor.check_pwned(e['password'])
                    if c > 0:
                        print(Fore.RED + f" ¡PWNED! ({c} veces)" + Style.RESET_ALL)
                        bad_count += 1
                    else:
                        print(Fore.GREEN + " OK" + Style.RESET_ALL)
                    time.sleep(0.1) 
                
                if bad_count > 0:
                    vault.add_audit_event(m_pass, s_key, "HIBP_ALERT", f"Scan found {bad_count} leaked passwords")
                    print(Fore.RED + f"\n[X] ALERTA: Tienes {bad_count} contraseñas filtradas." + Style.RESET_ALL)
                else:
                    vault.add_audit_event(m_pass, s_key, "HIBP_CLEAN", "Full scan passed successfully")
                    print(Fore.GREEN + "\n[✓] Tu bóveda es segura." + Style.RESET_ALL)
            # --- OPCIÓN 10: OSINT (Identity Tracer) ---
            elif op == '10':
                scanner = OsintScanner()
                print(Fore.YELLOW + "\n--- RECONOCIMIENTO DE HUELLA DIGITAL (OSINT) ---" + Style.RESET_ALL)
                target_user = input("Objetivo (Usuario o Email): ").strip()
                
                if target_user:
                    found = scanner.scan_target(target_user)
                    
                    print("-" * 50)
                    if found:
                        print(Fore.GREEN + f"[!] ÉXITO: Se encontraron {len(found)} coincidencias." + Style.RESET_ALL)
                        log_msg = f"OSINT Scan '{target_user}': {len(found)} matches found."
                        vault.add_audit_event(m_pass, s_key, "OSINT_HIT", log_msg)

                        if input(f"\n{Fore.CYAN}¿Generar reporte forense (JSON)? (s/n): {Style.RESET_ALL}").lower() == 's':
                            fname = scanner.save_report(target_user)
                            if fname:
                                print(f"{Fore.GREEN}[✓] Reporte guardado en: {fname}{Style.RESET_ALL}")
                                vault.add_audit_event(m_pass, s_key, "OSINT_EXPORT", f"Report generated: {fname}")
                    else:
                        print(Fore.YELLOW + "[i] Objetivo limpio. No se encontraron perfiles públicos (Top 100)." + Style.RESET_ALL)
                        vault.add_audit_event(m_pass, s_key, "OSINT_CLEAN", f"Scanned '{target_user}'. No matches.")
                    print("-" * 50)

    except Exception as e:
        print(Fore.RED + f"\n[!] Error/Auth Fallida: {e}" + Style.RESET_ALL)
        time.sleep(2) 

if __name__ == "__main__":
    run_cli()