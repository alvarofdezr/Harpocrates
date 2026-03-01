import os
import threading
import time
import shutil
import getpass
from colorama import Fore, Style
import pyperclip
from zxcvbn import zxcvbn

from core.exceptions import HIBPConnectionError, HarpocratesError, AuthenticationError
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
            ARCHITECTURE: Local Encrypted Vault | ALGORITHMS: Argon2id + AES-256-GCM (v1.2.0)
    ------------------------------------------------------------------------------------------
"""

def secure_copy(data: str) -> None:
    try:
        pyperclip.copy(data)
        print(f"\n[i] Clipboard: Data copied. It will be cleared in 20s.")
        def clear():
            time.sleep(20)
            pyperclip.copy("")
        threading.Thread(target=clear, daemon=True).start()
    except Exception:
        print(Fore.YELLOW + "[!] Could not access the clipboard." + Style.RESET_ALL)

def check_strength(pw: str) -> str:
    results = zxcvbn(pw)
    score = results['score']
    if score < 3:
        feedback = results['feedback']['warning']
        if not feedback and results['feedback']['suggestions']:
            feedback = results['feedback']['suggestions'][0]
        elif not feedback:
            feedback = "Add unpredictable words, numbers, or symbols."
        return f"{Fore.RED}WEAK (Score: {score}/4) - {feedback}{Style.RESET_ALL}"
    return f"{Fore.GREEN}STRONG (Score: {score}/4){Style.RESET_ALL}"

def entry_action_menu(vault, entry, index):
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
                vault.update_entry(index, chg)
                print(Fore.GREEN + "[✓] Updated successfully." + Style.RESET_ALL)
                break
        elif op == '3':
            if input("Delete? (y/n): ").lower() == 'y':
                vault.delete_entry(index)
                print(Fore.RED + "[✓] Deleted successfully." + Style.RESET_ALL)
                return True
        elif op == '4': break
    return False

def run_cli():
    print('\033[2J\033[H', end='') 
    print(BANNER)
    
    vault = VaultManager()
    crypto = HarpocratesCrypto()
    
    if not os.path.exists("vault.hpro"):
        m_pass = getpass.getpass("Create your Master Password: ")
        s_key = crypto.generate_secret_key()
        vault.create_new_vault(m_pass, s_key)
        
        print(f"\nSECRET KEY: {s_key}\nTHIS KEY WILL ONLY BE SHOWN NOW!")
        getpass.getpass("Save it in a secure place and press ENTER to continue...")
        print('\033[2J\033[H', end='')
        print(BANNER)
    
    m_pass = getpass.getpass("[?] Master Password: ")
    s_key = getpass.getpass("[?] Secret Key: ")
    
    try:
        vault.load_vault(m_pass, s_key)
        
        del m_pass
        del s_key 
        
        vault.add_audit_event("LOGIN", "Access via CLI")
        print(Fore.GREEN + "\n[✓] Access Granted." + Style.RESET_ALL)
        
        while True:
            print(f"\n{'-'*30} MAIN MENU v1.2.0 {'-'*40}")
            print("1.  List         2. Add         3. Search")
            print("4.  Generate     5. Import      6. Exit")
            print("7.  Backup       8. Audit Log   9. HIBP Scan")
            op = input("\n> ").strip()
            
            if op == '1':
                entries = vault.get_entries()
                print(f"\nID    | {'SERVICE':<40} | USERNAME")
                print("-" * 60)
                for i, e in enumerate(entries):
                    print(f"{i:<4} | {e['title']:<40} | {e['username']}")
                sel = input("\nID to manage (Enter to go back): ")
                if sel.isdigit() and int(sel) < len(entries):
                    entry_action_menu(vault, entries[int(sel)], int(sel))

            elif op == '2':
                t = ""
                while not t.strip():
                    t = input("Service (required): ").strip()
                
                u = ""
                while not u.strip():
                    u = input("Username (required): ").strip()
                
                gen_prompt = input("Auto-generate password? (y/n): ").lower()
                if gen_prompt == 'y':
                    p = PasswordGenerator.generate(24)
                    print(f"Generated Password: {Fore.GREEN}{p}{Style.RESET_ALL}")
                    if input("Copy to clipboard? (y/n): ").lower() == 'y': secure_copy(p)
                else:
                    p = ""
                    while not p:
                        p = getpass.getpass("Password (required): ")

                print(f"Strength: {check_strength(p)}")
                vault.add_entry(t, u, p, input("URL (optional): "), input("Notes (optional): "))
                print(Fore.GREEN + "[✓] Saved successfully." + Style.RESET_ALL)

            elif op == '3':
                q = input("Search: ").lower()
                entries = vault.get_entries()
                res = [(i,e) for i,e in enumerate(entries) if q in e['title'].lower()]
                for i, (idx, e) in enumerate(res): print(f"[{i}] {e['title']}")
                if res:
                    sel = input("Select ID: ")
                    if sel.isdigit() and int(sel) < len(res):
                        entry_action_menu(vault, res[int(sel)][1], res[int(sel)][0])

            elif op == '4':
                pw = PasswordGenerator.generate(32)
                print(f"Generated Password: {Fore.GREEN}{pw}{Style.RESET_ALL}")
                if input("Copy to clipboard? (y/n): ").lower() == 'y': secure_copy(pw)

            elif op == '5':
                path = input("CSV Path: ").strip('"')
                if input("Import? (y/n): ").lower() == 'y':
                    qty, msg = import_from_csv(path, vault) 
                    print(msg)
                    if qty > 0: vault.add_audit_event("IMPORT", f"Imported {qty} items")

            elif op == '6':
                print("\n[!] Closing session securely...")
                break

            elif op == '7':
                bk = f"backup_{os.urandom(6).hex()}.hpro"
                shutil.copy("vault.hpro", bk)
                if os.name == 'posix':
                    os.chmod(bk, 0o600)
                vault.add_audit_event("BACKUP", f"Created {bk}")
                print(Fore.GREEN + f"[✓] Backup created securely: {bk}" + Style.RESET_ALL)

            elif op == '8':
                logs = vault.get_logs()
                is_valid = vault.verify_log_integrity()
                status_color = Fore.GREEN if is_valid else Fore.RED
                status_text = "VALID" if is_valid else "COMPROMISED"
                
                print(Fore.CYAN + f"\n--- FORENSIC LOG ({len(logs)}) [CHAIN: {status_color}{status_text}{Fore.CYAN}] ---" + Style.RESET_ALL)
                for l in logs[:15]: 
                    print(f"{l['timestamp']} | {l['action']:<10} | {l['details']}")
                input("\nPress Enter to return...")

            elif op == '9':
                print(Fore.YELLOW + "\n[!] Connecting to HaveIBeenPwned (K-Anonymity)..." + Style.RESET_ALL)
                try:
                    entries = vault.get_entries()
                    bad_count = 0
                    
                    for e in entries:
                        print(f"[*] Analyzing {e['title']}...", end="", flush=True)
                        c = PasswordAuditor.check_pwned(e['password'])
                        if c > 0:
                            print(Fore.RED + f" PWNED! ({c} times)" + Style.RESET_ALL)
                            bad_count += 1
                        else:
                            print(Fore.GREEN + " OK" + Style.RESET_ALL)
                        time.sleep(1.5) 
                    
                    if bad_count > 0:
                        vault.add_audit_event("HIBP_ALERT", f"Scan found {bad_count} leaked passwords")
                        print(Fore.RED + f"\n[X] ALERT: You have {bad_count} leaked passwords." + Style.RESET_ALL)
                    else:
                        vault.add_audit_event("HIBP_CLEAN", "Full scan passed successfully")
                        print(Fore.GREEN + "\n[✓] Your vault is secure." + Style.RESET_ALL)
                
                except HIBPConnectionError as e:
                    print(Fore.RED + f"\n[!] Network Error during scan: {e}" + Style.RESET_ALL)

    except AuthenticationError:
        print(Fore.RED + "\n[!] Authentication Failed: Incorrect Master Password or Secret Key." + Style.RESET_ALL)
        time.sleep(2)
    except HarpocratesError as e:
        print(Fore.RED + f"\n[!] Vault Error: {e}" + Style.RESET_ALL)
        time.sleep(2)
    except Exception as e:
        print(Fore.RED + f"\n[!] Critical System Error: {e}" + Style.RESET_ALL)
        time.sleep(2)

if __name__ == "__main__":
    run_cli()