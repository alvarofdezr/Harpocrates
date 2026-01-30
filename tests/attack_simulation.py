import sys
import os
import time
from colorama import Fore, Style, init

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.vault import VaultManager
from core.crypto import HarpocratesCrypto

init()

def simulate_attack():
    print(Fore.RED + r"""
     _   _  ___   ___  _   __  _____  _____  ___  
    | | | |/ _ \ / __|| | / / |  ___||  _  |/ _ \ 
    | |_| / /_\ \ (__ | |/ /  | |__  | | | / /_\ \
    |  _  |  _  |\__ \|    \  |  __| | | | |  _  |
    | | | | | | |___| | |\  \ | |___ \ \_/ / | | |
    \_| |_|_| |_/\___/\_| \_/ \____/  \___/\_| |_/
            [ SIMULACIÓN DE ATAQUE ]
    """ + Style.RESET_ALL)

    vault_file = "victim_vault.hpro"
    target_password = "MySuperSecretPassword123!"
    
    print(f"[1] Generando bóveda víctima con password: {Fore.GREEN}{target_password}{Style.RESET_ALL}")
    
    crypto = HarpocratesCrypto()
    s_key = crypto.generate_secret_key()
    
    vault = VaultManager(vault_file)
    vault.create_new_vault(target_password, s_key)
    
    dictionary = [
        "123456",
        "password",
        "admin",
        "iloveyou",
        "harpocrates",
        "python",
        "qwerty",
        "MySuperSecretPassword123!" 
    ]

    print(f"\n[2] Iniciando ataque de diccionario ({len(dictionary)} intentos)...")
    print(Fore.YELLOW + "Fíjate en el tiempo que tarda cada intento (Argon2id en acción):" + Style.RESET_ALL)
    print("-" * 60)

    start_attack = time.time()

    for attempt in dictionary:
        print(f"[*] Probando password: {Fore.CYAN}{attempt:<25}{Style.RESET_ALL}", end="")
        
        t0 = time.time()
        try:
            vault.load_vault(attempt, s_key)
            
            dt = time.time() - t0
            print(f"-> {Fore.GREEN}¡CRACKED! ✅ {Style.RESET_ALL} (Tardó {dt:.4f}s)")
            print(f"\n{Fore.RED}[!] LA BÓVEDA HA SIDO VULNERADA CON: '{attempt}'{Style.RESET_ALL}")
            break
            
        except Exception:
            dt = time.time() - t0
            print(f"-> {Fore.RED}FALLÓ ❌ {Style.RESET_ALL} (Tardó {dt:.4f}s)")

    total_time = time.time() - start_attack
    print("-" * 60)
    print(f"Resumen del ataque:")
    print(f"Tiempo total: {total_time:.4f} segundos")
    print(f"Promedio por intento: {total_time/len(dictionary):.4f} segundos")

    if os.path.exists(vault_file):
        os.remove(vault_file)

if __name__ == "__main__":
    simulate_attack()