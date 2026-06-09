import os
import threading
import time
import shutil
import getpass
from colorama import Fore, Style  # type: ignore
import pyperclip  # type: ignore
from zxcvbn import zxcvbn  # type: ignore

from core.exceptions import (
    HIBPConnectionError,
    HarpocratesError,
    AuthenticationError,
    VaultMigrationRequired,
)
from core.vault import VaultManager
from core.crypto import HarpocratesCrypto
from core.generator import PasswordGenerator
from core.importer import import_from_csv
from core.auditor import PasswordAuditor
from core.secure_memory import SecureString

BANNER = r"""
    ██╗  ██╗ █████╗ ██████╗ ██████╗  ██████╗  ██████╗██████╗  █████╗ ████████╗███████╗███████╗
    ██║  ██║██╔══██╗██╔══██╗██╔══██╗██╔═══██╗██╔════╝██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██╔════╝
    ███████║███████║██████╔╝██████╔╝██║   ██║██║     ██████╔╝███████║   ██║   █████╗  ███████╗
    ██╔══██║██╔══██║██╔══██╗██╔═══╝ ██║   ██║██║     ██╔══██╗██╔══██║   ██║   ██╔══╝  ╚════██║
    ██║  ██║██║  ██║██║  ██║██║     ╚██████╔╝╚██████╗██║  ██║██║  ██║   ██║   ███████╗███████║
    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝      ╚═════╝  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚══════╝
                                    [ SILENCE IS SECURITY ]
    ------------------------------------------------------------------------------------------
            ARCHITECTURE: Local Encrypted Vault | ALGORITHMS: Argon2id + AES-256-GCM (v2.0.0)
    ------------------------------------------------------------------------------------------
"""

INACTIVITY_TIMEOUT = 300  # 5 minutes
last_activity_time = time.time()


def update_activity() -> None:
    global last_activity_time
    last_activity_time = time.time()


def auto_lock_monitor() -> None:
    while True:
        time.sleep(5)
        if time.time() - last_activity_time > INACTIVITY_TIMEOUT:
            print(
                Fore.RED
                + "\n[!] Session locked due to inactivity. Exiting for security."
                + Style.RESET_ALL
            )
            os._exit(0)


def secure_copy(data: str) -> None:
    try:
        pyperclip.copy(data)
        print("\n[i] Clipboard: data copied. It will be cleaned in 20 s.")
    except pyperclip.PyperclipException:
        print(Fore.YELLOW + "[!] Could not copy to clipboard." + Style.RESET_ALL)
        return

    def clear() -> None:
        time.sleep(20)
        try:
            pyperclip.copy("")
        except pyperclip.PyperclipException:
            pass

    t = threading.Thread(target=clear, daemon=True)
    t.start()


def check_strength(pw: str) -> str:
    results = zxcvbn(pw)
    score = results["score"]
    if score < 3:
        feedback = results["feedback"]["warning"]
        if not feedback and results["feedback"]["suggestions"]:
            feedback = results["feedback"]["suggestions"][0]
        elif not feedback:
            feedback = "Add unpredictable words, numbers, or symbols."
        return f"{Fore.RED}WEAK (Score: {score}/4) - {feedback}{Style.RESET_ALL}"
    return f"{Fore.GREEN}STRONG (Score: {score}/4){Style.RESET_ALL}"


class CommandDispatcher:
    def __init__(self, vault: VaultManager):
        self.vault = vault
        self.commands = {
            "1": self.cmd_list,
            "2": self.cmd_search,
            "3": self.cmd_add,
            "4": self.cmd_generate,
            "5": self.cmd_import,
            "6": self.cmd_backup,
            "7": self.cmd_audit,
            "8": self.cmd_hibp,
            "9": self.cmd_exit,
        }

    def dispatch(self, op: str) -> bool:
        update_activity()
        cmd = self.commands.get(op)
        if cmd:
            return cmd()
        return True  # Continue loop if invalid command

    def entry_action_menu(self, entry: dict[str, str], index: int) -> bool:
        while True:
            update_activity()
            print(
                f"\nService: {Fore.CYAN}{entry['title']}{Style.RESET_ALL} | Username: {entry['username']}"
            )
            if entry.get("notes"):
                print(f"Notes: {Fore.YELLOW}{entry['notes']}{Style.RESET_ALL}")

            print("\n1. Copy Password  2. Edit  3. Delete  4. Back")
            op = input("> ")
            update_activity()

            if op == "1":
                secure_copy(entry["password"])
                break
            elif op == "2":
                print("--- Leave empty to keep unchanged ---")
                chg = {}
                for field in ["title", "username", "password", "url", "notes"]:
                    val = input(f"{field.capitalize()}: ")
                    if val:
                        chg[field] = val
                if chg:
                    self.vault.update_entry(index, chg)
                    print(Fore.GREEN + "[✓] Updated successfully." + Style.RESET_ALL)
                    break
            elif op == "3":
                if input("Delete? (y/n): ").lower() == "y":
                    self.vault.delete_entry(index)
                    print(Fore.RED + "[✓] Deleted successfully." + Style.RESET_ALL)
                    return True
            elif op == "4":
                break
        return False

    def cmd_list(self) -> bool:
        entries = self.vault.get_entries()
        print(f"\nID    | {'SERVICE':<40} | USERNAME")
        print("-" * 60)
        for i, e in enumerate(entries):
            print(f"{i:<4} | {e['title']:<40} | {e['username']}")
        sel = input("\nID to manage (Enter to go back): ")
        if sel.isdigit() and int(sel) < len(entries):
            self.entry_action_menu(entries[int(sel)], int(sel))
        return True

    def cmd_add(self) -> bool:
        t = ""
        while not t.strip():
            t = input("Service (required): ").strip()
        u = ""
        while not u.strip():
            u = input("Username (required): ").strip()

        gen_prompt = input("Auto-generate password? (y/n): ").lower()
        if gen_prompt == "y":
            p = PasswordGenerator.generate(24)
            print(f"Generated Password: {Fore.GREEN}{p}{Style.RESET_ALL}")
            if input("Copy to clipboard? (y/n): ").lower() == "y":
                secure_copy(p)
        else:
            p = ""
            while not p:
                p = getpass.getpass("Password (required): ")

        print(f"Strength: {check_strength(p)}")
        self.vault.add_entry(
            t, u, p, input("URL (optional): "), input("Notes (optional): ")
        )
        print(Fore.GREEN + "[✓] Saved successfully." + Style.RESET_ALL)
        return True

    def cmd_search(self) -> bool:
        q = input("Search: ").lower()
        entries = self.vault.get_entries()
        res = [(i, e) for i, e in enumerate(entries) if q in e["title"].lower()]
        for i, (idx, e) in enumerate(res):
            print(f"[{i}] {e['title']}")
        if res:
            sel = input("Select ID: ")
            if sel.isdigit() and int(sel) < len(res):
                self.entry_action_menu(res[int(sel)][1], res[int(sel)][0])
        return True

    def cmd_generate(self) -> bool:
        pw = PasswordGenerator.generate(32)
        print(f"Generated Password: {Fore.GREEN}{pw}{Style.RESET_ALL}")
        if input("Copy to clipboard? (y/n): ").lower() == "y":
            secure_copy(pw)
        return True

    def cmd_import(self) -> bool:
        path = input("CSV Path: ").strip('"')
        if input("Import? (y/n): ").lower() == "y":
            qty, msg = import_from_csv(path, self.vault)
            print(msg)
            if qty > 0:
                self.vault.add_audit_event("IMPORT", f"Imported {qty} items")
        return True

    def cmd_exit(self) -> bool:
        print("\n[!] Closing session securely...")
        return False

    def cmd_backup(self) -> bool:
        import os as os_mod

        bk = f"backup_{os_mod.urandom(6).hex()}.hpro"
        shutil.copy("vault.hpro", bk)
        if os.name == "posix":
            os.chmod(bk, 0o600)
        self.vault.add_audit_event("BACKUP", f"Created {bk}")
        print(Fore.GREEN + f"[✓] Backup created securely: {bk}" + Style.RESET_ALL)
        return True

    def cmd_audit(self) -> bool:
        logs = self.vault.get_logs()
        is_valid = self.vault.verify_log_integrity()
        status_color = Fore.GREEN if is_valid else Fore.RED
        status_text = "VALID" if is_valid else "COMPROMISED"

        print(
            Fore.CYAN
            + f"\n--- FORENSIC LOG ({len(logs)}) [CHAIN: {status_color}{status_text}{Fore.CYAN}] ---"
            + Style.RESET_ALL
        )
        for log_entry in logs[:15]:
            print(f"{log_entry['timestamp']} | {log_entry['action']:<10} | {log_entry['details']}")
        input("\nPress Enter to return...")
        return True

    def cmd_hibp(self) -> bool:
        print(
            Fore.YELLOW
            + "\n[!] Connecting to HaveIBeenPwned (K-Anonymity)..."
            + Style.RESET_ALL
        )
        try:
            entries = self.vault.get_entries()
            bad_count = 0

            for e in entries:
                print(f"[*] Analyzing {e['title']}...", end="", flush=True)
                c = PasswordAuditor.check_pwned(e["password"])
                if c > 0:
                    print(Fore.RED + f" PWNED! ({c} times)" + Style.RESET_ALL)
                    bad_count += 1
                else:
                    print(Fore.GREEN + " OK" + Style.RESET_ALL)
                time.sleep(1.5)

            if bad_count > 0:
                self.vault.add_audit_event(
                    "HIBP_ALERT", f"Scan found {bad_count} leaked passwords"
                )
                print(
                    Fore.RED
                    + f"\n[X] ALERT: You have {bad_count} leaked passwords."
                    + Style.RESET_ALL
                )
            else:
                self.vault.add_audit_event(
                    "HIBP_CLEAN", "Full scan passed successfully"
                )
                print(Fore.GREEN + "\n[✓] Your vault is secure." + Style.RESET_ALL)

        except HIBPConnectionError as e:
            print(Fore.RED + f"\n[!] Network Error during scan: {e}" + Style.RESET_ALL)
        return True


def _handle_new_vault(vault: VaultManager, crypto: HarpocratesCrypto) -> None:
    m_pass_raw = getpass.getpass("Create your Master Password: ")
    s_key_raw = crypto.generate_secret_key()

    with SecureString(m_pass_raw) as m_pass_sec, SecureString(s_key_raw) as s_key_sec:
        vault.create_new_vault(m_pass_sec.decode("utf-8"), s_key_sec.decode("utf-8"))

    print(f"\nSECRET KEY: {s_key_raw}\nTHIS KEY WILL ONLY BE SHOWN NOW!")
    getpass.getpass("Save it in a secure place and press ENTER to continue...")

    print("\033[2J\033[H", end="")
    print(BANNER)


def _authenticate_vault(vault: VaultManager) -> bool:
    m_pass_raw = getpass.getpass("[?] Master Password: ")
    s_key_raw = getpass.getpass("[?] Secret Key: ")

    try:
        with (
            SecureString(m_pass_raw) as m_pass_sec,
            SecureString(s_key_raw) as s_key_sec,
        ):
            vault.load_vault(m_pass_sec.decode("utf-8"), s_key_sec.decode("utf-8"))

        vault.add_audit_event("LOGIN", "Access via CLI")
        print(Fore.GREEN + "\n[✓] Access Granted." + Style.RESET_ALL)
        return True

    except VaultMigrationRequired:
        print(
            Fore.YELLOW
            + "\n[!] WARNING: Vault is using an older format (v1.x)."
            + Style.RESET_ALL
        )
        ans = input("Migrate vault to v2 format? (y/n): ")
        if ans.lower() == "y":
            vault.migrate_to_v2()
            vault.add_audit_event("SYSTEM", "Vault migrated to v2.0.0 format")
            print(
                Fore.GREEN
                + "[✓] Migration successful. Access Granted."
                + Style.RESET_ALL
            )
            return True
        else:
            print(Fore.RED + "\n[!] Migration cancelled. Exiting..." + Style.RESET_ALL)

    except AuthenticationError:
        print(
            Fore.RED
            + "\n[!] Authentication Failed: Incorrect Master Password or Secret Key."
            + Style.RESET_ALL
        )
        time.sleep(2)
    except HarpocratesError as e:
        print(Fore.RED + f"\n[!] Vault Error: {e}" + Style.RESET_ALL)
        time.sleep(2)
    except Exception as e:
        print(Fore.RED + f"\n[!] Critical System Error: {e}" + Style.RESET_ALL)
        time.sleep(2)

    return False


def run_cli() -> None:
    print("\033[2J\033[H", end="")
    print(BANNER)

    vault = VaultManager()
    crypto = HarpocratesCrypto()

    # Start auto-lock monitor thread
    monitor_thread = threading.Thread(target=auto_lock_monitor, daemon=True)
    monitor_thread.start()

    if not os.path.exists(vault.vault_path):
        _handle_new_vault(vault, crypto)

    if _authenticate_vault(vault):
        dispatcher = CommandDispatcher(vault)
        while True:
            update_activity()
            print(f"\n{'-'*30} MAIN MENU v2.0.0 {'-'*40}")
            print("1. List         2. Search      3. Add")
            print("4. Generate     5. Import      6. Backup")
            print("7. Audit Log    8. HIBP Scan   9. Exit")
            op = input("\n> ").strip()

            if not dispatcher.dispatch(op):
                break


if __name__ == "__main__":
    run_cli()
