import sys
from app.cli import run_cli

def main():
    try:
        run_cli()
    except KeyboardInterrupt:
        print("\n\n[!] Interruption detected. Closing vault forcefully...")
    except Exception as e:
        print(f"\n[X] Error unexpected in the core: {e}")
    finally:
        sys.exit(0)

if __name__ == "__main__":
    main()