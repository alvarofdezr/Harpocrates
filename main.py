import sys
import gc
from app.cli import run_cli

def wipe_sensitive_data():
    """
    Intento de mitigación para limpiar referencias en RAM antes de cerrar.
    """
    if 'm_pass' in locals(): m_pass = None
    if 's_key' in locals(): s_key = None
    
    gc.collect()
    print("\n[!] Memoria volatilizada. Harpocrates vuelve al silencio.")

def main():
    try:
        run_cli()
    except KeyboardInterrupt:
        print("\n\n[!] Interrupción detectada. Cerrando bóveda forzosamente...")
    except Exception as e:
        print(f"\n[X] Error inesperado en el núcleo: {e}")
    finally:
        wipe_sensitive_data()
        sys.exit(0)

if __name__ == "__main__":
    main()