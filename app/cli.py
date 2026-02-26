import os
import threading
import time
import shutil
import re
from datetime import datetime
from colorama import Fore, Style
import pyperclip

from core.vault import VaultManager
from core.crypto import HarpocratesCrypto
from core.generator import PasswordGenerator
from core.importer import import_from_csv
from core.auditor import PasswordAuditor   

BANNER = r"""
    ██╗  ██╗ █████╗ ██████╗ ██████╗  ██████╗  ██████╗██████╗  █████╗ ████████╗███████╗███████╗
    ██║  ██║██╔══██╗██╔══██╗██╔══██╗██╔═══██╗██╔════╝██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██╔════╝
    ███████║███████║██████╔╝██████╔╝██║   ██║██║     ██████╔╝███████║   ██║   █████╗  ███████╗
    ██╔══██║██╔══██║██╔══██╗██╔═══╝ ██║   ██║██║     ██╔══██╗██╔══██║   ██║   ██╔══╝  ╚════██║
    ██║  ██║██║  ██║██║  ██║██║     ╚██████╔╝╚██████╗██║  ██║██║  ██║   ██║   ███████╗███████║
    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝      ╚═════╝  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚══════╝
                                    [ SILENCE IS SECURITY ]
    ------------------------------------------------------------------------------------------
            ARCHITECTURE: Zero-Knowledge | ALGORITHMS: Argon2id + AES-256-GCM (v1.5.1)
    ------------------------------------------------------------------------------------------
"""

def secure_copy(data):
    """
    Copies data to the clipboard securely and clears it after a timeout.
    Uses a background thread to clear the clipboard to avoid blocking the UI.
    """
    try:
        pyperclip.copy(data)
        print(f"\n[i] Clipboard: Data copied. Will be cleared in 20s.")
        def clear():
            time.sleep(20)
            if pyperclip.paste() == data:
                pyperclip.copy("")
        threading.Thread(target=clear, daemon=True).start()
    except Exception:
        print(Fore.YELLOW + "[!] Could not access clipboard." + Style.RESET_ALL)

def check_strength(pw):
    """
    Evaluates the strength of a password based on length and character variety.
    Returns a colored string indicating 'WEAK' or 'STRONG'.
    """
    s=0
    if len(pw)>=12: s+=1
    if re.search(r"\d", pw): s+=1
    if re.search(r"[A-Z]", pw): s+=1
    if re.search(r"[!@#$%^&*]", pw): s+=1
    if s<3: return Fore.RED + "WEAK" + Style.RESET_ALL
    return Fore.GREEN + "STRONG" + Style.RESET_ALL

def entry_action_menu(vault, m_pass, s_key, entry, index):
    """
    Displays the management submenu for a specific vault entry.
    Allows copying password, editing fields, or deleting the entry.
    """
    while True:
        print(f"\nService: {Fore.CYAN}{entry['title']}{Style.RESET_ALL} | Username: {entry['username']}")
        if entry.get('notes'): print(f"Notes: {Fore.YELLOW}{entry['notes']}{Style.RESET_ALL}")
        
        print("\n1. Copy Password  2. Edit  3. Delete  4. Back")
        op = input("> ")
        
        if op == '1':
            secure_copy(entry['password'])
            break
        elif op == '2':
            print("--- Leave empty to keep unchanged ---")
            chg = {}
            for field in ['title', 'username', 'password', 'url', 'notes']:
                val = input(f"{field.capitalize()}: ") 
                if val: chg[field] = val
            if chg:
                vault.update_entry(m_pass, s_key, index, chg)
                print(Fore.GREEN + "[✓] Updated successfully." + Style.RESET_ALL)
                break
        elif op == '3':
            if input("Delete? (y/n): ") == 'y':
                vault.delete_entry(m_pass, s_key, index)
                print(Fore.RED + "[✓] Deleted." + Style.RESET_ALL)
                return True
        elif op == '4': break
    return False

def run_cli():
    """
    Main entry point for the Command Line Interface.
    Handles authentication, main menu navigation, and user interactions.
    """
    os.system('cls' if os.name == 'nt' else 'clear') # nosec
    print(BANNER)
    
    vault = VaultManager()
    crypto = HarpocratesCrypto()
    
    if not os.path.exists("vault.hpro"):
        m_pass = input("Create your Master Password: ")
        s_key = crypto.generate_secret_key()
        vault.create_new_vault(m_pass, s_key)
        print(f"\nSECRET KEY: {s_key}\nSAVE IT!")
    
    m_pass = input("[?] Master Password: ")
    s_key = input("[?] Secret Key: ")
    
    try:
        vault.load_vault(m_pass, s_key)
        vault.add_audit_event(m_pass, s_key, "LOGIN", "Access via CLI")
        print(Fore.GREEN + "\n[✓] Access Granted." + Style.RESET_ALL)
        
        while True:
            print(f"\n{'-'*40} MENU v1.5.1 {'-'*40}")
            print("1.  List         2. Add         3. Search")
            print("4.  Generate     5. Import      6. Exit")
            print("7.  Backup       8. View Logs   9. HIBP Scanner")
            op = input("\n> ").strip()
            
            if op == '1':
                data = vault.data 
                entries = data.get('entries', [])
                print(f"\nID    | {'SERVICE':<40} | USERNAME")
                print("-" * 60)
                for i, e in enumerate(entries):
                    print(f"{i:<4} | {e['title']:<40} | {e['username']}")
                sel = input("\nID to manage (Enter to go back): ")
                if sel.isdigit() and int(sel) < len(entries):
                    entry_action_menu(vault, m_pass, s_key, entries[int(sel)], int(sel))

            elif op == '2':
                t = input("Service: ")
                u = input("Username: ")
                p = PasswordGenerator.generate(24) if input("Auto-generate? (y/n): ")=='y' else input("Password: ")
                print(check_strength(p))
                vault.add_entry(m_pass, s_key, t, u, p, input("URL: "), input("Notes: "))
                print("[✓] Saved.")

            elif op == '3':
                q = input("Search: ").lower()
                data = vault.data
                res = [(i,e) for i,e in enumerate(data['entries']) if q in e['title'].lower()]
                for i, (idx, e) in enumerate(res): print(f"[{i}] {e['title']}")
                if res:
                    sel = input("Select ID: ")
                    if sel.isdigit() and int(sel) < len(res):
                        entry_action_menu(vault, m_pass, s_key, res[int(sel)][1], res[int(sel)][0])

            elif op == '4':
                pw = PasswordGenerator.generate(32)
                print(f"Password: {Fore.GREEN}{pw}{Style.RESET_ALL}")
                if input("Copy? (y/n): ")=='y': secure_copy(pw)

            elif op == '5':
                path = input("CSV File: ").strip('"')
                if input("Import? (y/n): ")=='y':
                    qty, msg = import_from_csv(path, vault, s_key, m_pass)
                    print(msg)
                    if qty > 0: vault.add_audit_event(m_pass, s_key, "IMPORT", f"Imported {qty} items")

            elif op == '6': 
                print("\n[!] Closing session securely...")
                break

            elif op == '7':
                bk = f"backup_{datetime.now().strftime('%Y%m%d_%H%M')}.hpro"
                shutil.copy("vault.hpro", bk)
                vault.add_audit_event(m_pass, s_key, "BACKUP", f"Created {bk}")
                print(f"[✓] Backup: {bk}")

            elif op == '8':
                data = vault.data 
                logs = data.get('logs', [])
                print(Fore.CYAN + f"\n--- FORENSIC LOG ({len(logs)}) ---" + Style.RESET_ALL)
                for l in logs[:15]: 
                    print(f"{l['timestamp']} | {l['action']:<10} | {l['details']}")
                input("\nPress Enter to return...")

            elif op == '9':
                print(Fore.YELLOW + "\n[!] Connecting to HaveIBeenPwned (K-Anonymity)..." + Style.RESET_ALL)
                data = vault.data 
                bad_count = 0
                
                for e in data['entries']:
                    print(f"[*] Analyzing {e['title']}...", end="", flush=True)
                    c = PasswordAuditor.check_pwned(e['password'])
                    if c > 0:
                        print(Fore.RED + f" PWNED! ({c} times)" + Style.RESET_ALL)
                        bad_count += 1
                    else:
                        print(Fore.GREEN + " OK" + Style.RESET_ALL)
                    time.sleep(0.1) 
                
                if bad_count > 0:
                    vault.add_audit_event(m_pass, s_key, "HIBP_ALERT", f"Scan found {bad_count} leaked passwords")
                    print(Fore.RED + f"\n[X] ALERT: You have {bad_count} leaked passwords." + Style.RESET_ALL)
                else:
                    vault.add_audit_event(m_pass, s_key, "HIBP_CLEAN", "Full scan passed successfully")
                    print(Fore.GREEN + "\n[✓] Your vault is secure." + Style.RESET_ALL)

    except Exception as e:
        print(Fore.RED + f"\n[!] Error/Auth Failed: {e}" + Style.RESET_ALL)
        time.sleep(2) 

if __name__ == "__main__":
    run_cli()