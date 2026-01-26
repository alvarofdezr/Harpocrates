import os
from dotenv import load_dotenv
from core.vault import VaultManager
from core.crypto import HarpocratesCrypto
from core.generator import PasswordGenerator

load_dotenv()

BANNER = r"""
      _   _                                            _            
     | | | | __ _ _ __ _ __   ___   ___ _ __ __ _  ___| |_ ___  ___ 
     | |_| |/ _` | '__| '_ \ / _ \ / __| '__/ _` |/ __| __/ _ \/ __|
     |  _  | (_| | |  | |_) | (_) | (__| | | (_| | (__| ||  __/\__ \
     |_| |_|\__,_|_|  | .__/ \___/ \___|_|  \__,_|\___|\__\___||___/
                      |_|       [ SILENCE IS SECURITY ]
    ----------------------------------------------------------------
    [+] Zero-Knowledge Architecture | Argon2id | AES-256-GCM
    ----------------------------------------------------------------
"""

def run_cli():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(BANNER)
    
    crypto = HarpocratesCrypto()
    vault_path = os.getenv("VAULT_PATH", "default.hpro")
    vault = VaultManager(vault_path)

    m_pass = input("[?] Master Password: ")
    
    if not os.path.exists(vault_path):
        print("[!] Bóveda no detectada. Iniciando proceso de creación...")
        s_key = crypto.generate_secret_key()
        vault.create_new_vault(m_pass, s_key)
        print(f"\n[!!!] GUARDA TU SECRET KEY: {s_key}")
        print("[!] Sin esto y la contraseña, los datos se perderán para siempre.\n")
    else:
        s_key = input("[?] Secret Key: ")

    try:
        vault.load_vault(m_pass, s_key)
        print("\n[✓] Acceso Concedido.\n")
        
        while True:
            print(f"\n{'='*40}")
            print(f" HARPOCRATES TERMINAL - MODO SEGURO")
            print(f"{'='*40}")
            print("1. [L] Listar todas las entradas")
            print("2. [A] Añadir nueva credencial")
            print("3. [G] Generador de contraseñas")
            print("4. [B] Buscar entrada por servicio/usuario")
            print("5. [S] Salir y cerrar bóveda")

            opcion = input("\nHarpocrates > ").lower().strip()

            if opcion in ['1', 'l', 'listar']:
                data = vault.load_vault(m_pass, s_key)
                entries = data.get('entries', [])
                
                if not entries:
                    print("\n[!] La bóveda está vacía.")
                else:
                    print(f"\n{'SERVICIO':<20} | {'USUARIO':<20} | {'PASSWORD'}")
                    print("-" * 60)
                    for e in entries:
                        print(f"{e['title']:<20} | {e['username']:<20} | {e['password']}")
            
            elif opcion in ['2', 'a', 'añadir']:
                title = input("Servicio/Web: ")
                user = input("Usuario/Email: ")
                url = input("URL (opcional): ")
                
                print("\n[G] ¿Deseas generar una contraseña segura? (s/n)")
                if input("> ").lower() == 's':
                    from core.generator import PasswordGenerator
                    password = PasswordGenerator.generate(length=24)
                    print(f"[!] Contraseña generada: {password}")
                else:
                    password = input("Introduce la contraseña: ")
                
                vault.add_entry(m_pass, s_key, title, user, password, url)
                print("\n[✓] Entrada cifrada y guardada.")

            elif opcion in ['3', 'g', 'generar']:
                from core.generator import PasswordGenerator
                print(f"\n[+] Password Sugerida: {PasswordGenerator.generate(32)}")

            elif opcion in ['4', 'b', 'buscar']:
                query = input("[?] Término de búsqueda (Servicio o Usuario): ").lower().strip()
                data = vault.load_vault(m_pass, s_key)
                entries = data.get('entries', [])
                
                results = [
                    e for e in entries 
                    if query in e['title'].lower() or 
                        query in e['username'].lower() or 
                        query in e.get('url', '').lower()
                ]

                if not results:
                    print(f"\n[!] No se encontraron coincidencias para: '{query}'")
                else:
                    print(f"\n[✓] Resultados encontrados ({len(results)}):")
                    print(f"{'SERVICIO':<20} | {'USUARIO':<20} | {'PASSWORD'}")
                    print("-" * 60)
                    for e in results:
                        print(f"{e['title']:<20} | {e['username']:<20} | {e['password']}")
                        
            elif opcion in ['5', 's', 'salir', 'exit']:
                print("\n[!] Limpiando búfer de memoria... Bóveda cerrada.")
                break
            
            else:
                print("\n[?] Comando no reconocido.")
                
    except Exception as e:
        print(f"\n[X] Error Crítico: {e}")