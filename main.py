import sys
from app.cli import run_cli
from core.exceptions import HarpocratesError

def main():
    try:
        run_cli()
    except KeyboardInterrupt:
        print("\n\n[!] Interruption detected. Closing vault forcefully...")
    except HarpocratesError as e:
        print(f"\n[X] Vault error: {e}")
    except Exception as e:
        print(f"\n[X] Unexpected system error: {e}")
    finally:
        sys.exit(0)

if __name__ == "__main__":
    main()