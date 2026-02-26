import subprocess
import sys
import time
from colorama import Fore, Style, init

init()

def run_command(command, description):
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[*] Ejecutando: {description}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    start_time = time.time()
    
    result = subprocess.run(command, shell=True)
    
    elapsed = time.time() - start_time
    
    if result.returncode == 0:
        print(f"\n{Fore.GREEN}[✓] {description} PASÓ con éxito ({elapsed:.2f}s).{Style.RESET_ALL}")
        return True
    else:
        print(f"\n{Fore.RED}[X] {description} FALLÓ ({elapsed:.2f}s).{Style.RESET_ALL}")
        return False

def main():
    print(f"{Fore.MAGENTA}=== HARPOCRATES LOCAL CI/CD PIPELINE ==={Style.RESET_ALL}")
    
    steps = [
        ("python -m unittest discover tests -v", "Unit Tests (Core & Crypto)"),
        ("bandit -r core/ app/ -f screen", "Bandit (Static Security Analysis)"),
        ("pip-audit -r requirements.txt", "pip-audit (Dependency Vulnerability Scan)")
    ]
    
    all_passed = True
    
    for cmd, desc in steps:
        if not run_command(cmd, desc):
            all_passed = False
            break 
            
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    if all_passed:
        print(f"{Fore.GREEN}🎉 PIPELINE COMPLETADO: Tu código está listo para subir a GitHub. 🎉{Style.RESET_ALL}")
        sys.exit(0)
    else:
        print(f"{Fore.RED}⚠️ PIPELINE DETENIDO: Arregla los errores antes de hacer commit. ⚠️{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()