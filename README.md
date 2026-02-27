<p align="center">
  <img src="img/icono.png" width="300" height="300" alt="Harpocrates Logo">
</p>

---
# 🔐 Harpocrates Vault v1.6.0
> **Local Encrypted Vault Password Manager | Argon2id + AES-256-GCM**

![Security Status](https://github.com/alvarofdezr/Harpocrates/actions/workflows/security-test.yml/badge.svg?branch=main)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Release](https://img.shields.io/badge/Release-v1.6.0-blue)

**Harpocrates** is a robust Command Line Interface (CLI) password manager built for maximum security and privacy. It features a **Local Encrypted Vault** architecture, meaning the application never stores or knows your master password.

## 🚀 What's New in v1.6.0 (Security & Architecture Update)

This major release addresses critical architectural findings from a comprehensive senior security audit, transforming Harpocrates from a functional script into a robust, defensively programmed application.

**🛡️ Security & Core Architecture**
* **Atomic Writes:** Eliminated a destructive race condition in `save_vault`. Disk writes now use `os.replace` for atomic write-then-rename, guaranteeing the vault cannot be corrupted during a sudden power loss or crash.
* **Strict Encapsulation:** Internal state is now protected. Methods like `get_entries()` now return a `deepcopy`, preventing external code from mutating the vault without passing through proper transaction methods.
* **Transactional Bulk Imports:** `import_from_csv` now uses an atomic buffer. If a disk write fails midway, the vault's memory state performs a deepcopy rollback to prevent data corruption.
* **Path Traversal Protection:** Normalized vault paths using `os.path.abspath` to prevent directory traversal attacks during instantiation.
* **Honest Threat Modeling:** Documented Python's garbage collection limitations regarding in-memory string persistence for master keys.

**🔍 Auditor & HIBP API**
* **API Caching:** The in-memory HIBP cache prevents redundant network calls during bulk scans, significantly improving performance without writing any hashes to disk.
* **Strict Network Handling:** Replaced silent failures with explicit `HIBPConnectionError` exceptions to prevent false "Secure" flags when the API is unreachable.
* **Test Idempotency:** Added a cache-clearing mechanism to prevent state bleed between unit tests.

**💻 CLI & Features**
* **Real Entropy Checks:** Replaced the legacy regex strength checker with `zxcvbn`, the industry standard for password strength estimation and pattern detection.
* **Input Validation:** Enforced mandatory fields (Service, Username, Password) during manual entry creation.
* **Unconditional Clipboard Clearing:** Removed race conditions in the clipboard manager to ensure passwords are wiped exactly after 20 seconds.
* **Granular Error Handling:** Implemented custom exceptions (`AuthenticationError`, `VaultCorruptError`, `VaultNotFoundError`) replacing generic exception swallowing for accurate user feedback.

**⚙️ Engineering & Quality**
* **Modern Packaging:** Deprecated `setup.py` in favor of standard `pyproject.toml`.
* **Static Analysis:** Introduced comprehensive Type Hints across core modules (`importer.py`, `crypto.py`) for `mypy` consistency.
* **Test Isolation:** Renamed all unit tests to descriptive, independent names, removing numbered execution anti-patterns.


## 🛡️ Security Architecture

Harpocrates relies on industry-standard cryptography:

| Component | Technology | Description |
|-----------|------------|-------------|
| **KDF** | **Argon2id** | Configured with 64MB RAM cost to resist GPU cracking farms. |
| **Encryption** | **AES-256-GCM** | Authenticated Encryption (AEAD). Guarantees confidentiality and integrity. |
| **Audit** | **Encrypted Logs** | Event logs are stored *inside* the encrypted blob. Only the owner can read the history. |
| **Privacy** | **K-Anonymity** | Uses SHA-1 prefixing (5 chars) to query breach databases anonymously. |


## 🚀 Installation & Usage

### Option A: Binary (Windows)
No Python required. Plug and play.
1. Go to [Releases](../../releases).
2. Download the latest `Harpocrates.exe`.
3. Run it from your terminal or CMD.

### Option B: From Source (Developers)
1. **Clone and Setup:**
    ```bash
    git clone https://github.com/alvarofdezr/Harpocrates.git
    cd Harpocrates
    python -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate
    pip install . 
    ```
2. **Run:**
    ```bash
    python main.py
    ```
3. **📖 Usage:**
    ```plaintext
    
    ██╗  ██╗ █████╗ ██████╗ ██████╗  ██████╗  ██████╗██████╗  █████╗ ████████╗███████╗███████╗
    ██║  ██║██╔══██╗██╔══██╗██╔══██╗██╔═══██╗██╔════╝██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██╔════╝
    ███████║███████║██████╔╝██████╔╝██║   ██║██║     ██████╔╝███████║   ██║   █████╗  ███████╗
    ██╔══██║██╔══██║██╔══██╗██╔═══╝ ██║   ██║██║     ██╔══██╗██╔══██║   ██║   ██╔══╝  ╚════██║
    ██║  ██║██║  ██║██║  ██║██║     ╚██████╔╝╚██████╗██║  ██║██║  ██║   ██║   ███████╗███████║
    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝      ╚═════╝  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚══════╝
                                    [ SILENCE IS SECURITY ]
    ------------------------------------------------------------------------------------------
            ARCHITECTURE: Local Encrypted Vault | ALGORITHMS: Argon2id + AES-256-GCM (v1.6.0)
    ------------------------------------------------------------------------------------------

    [?] Master Password: 
    [?] Secret Key: 

    [✓] Access Granted: Vault decrypted in memory.

    ----------------------------- Main Menu (v1.6.0) ------------------------------ 
    [1] List         -> View accounts. Select an ID to Copy Password, Edit, or Delete.
    [2] Add          -> Store a new credential (includes strength meter).
    [3] Search       -> Deep search by service name or username.
    [4] Generate     -> Create high-entropy passwords (32 chars).
    [5] Import       -> Batch import from CSV.
    [6] Exit         -> Clears session references and closes.
    [7] Backup       -> Create a timestamped copy of your vault (e.g., backup_20241027.hpro).
    [8] Audit Log    -> Inspect the internal Forensic Event History.
    [9] HIBP Scan    -> Check your vault against 8 billion leaked passwords.

    Harpocrates >
    ```

## 🚨 Security testing
You can verify the resistance of the vault against brute-force attacks by running the included simulation script:
```bash
python tests/attack_simulation.py
```
To run the full suite of unit tests (covering cryptography, in-memory caching, and data integrity):
```bash
python -m unittest -v tests/test_core.py
```

## 🔄 Data Flow (Local Encrypted Vault)

1. **Input:** User provides Master Password + Secret Key.
2. **Derivation:** Argon2id processes inputs with a unique Salt.
3. **Encryption:** AES-256-GCM encrypts the JSON vault.
4. **Storage:** Only the Salt, Nonce, and Ciphertext are written to `.hpro`.
5. **Security:** The Master Password and Keys are never stored on disk.

## 🔒 Threat Model & Mitigations

| Threat | Mitigation |
| :--- | :--- |
| **Brute Force (Online)** | Argon2id with high memory cost makes local cracking attempts computationally expensive. |
| **Vault Theft** | Even with the `.hpro` file, an attacker needs BOTH the Master Password and the 128-bit Secret Key. |
| **Data Tampering** | AES-GCM provides AEAD (Authenticated Encryption with Associated Data). Any modification to the encrypted file results in a decryption failure. |
| **Memory Persistence** | Python's memory management (Garbage Collection) does not guarantee immediate zeroing of sensitive variables. The `del` statement removes the local reference but the garbage collector does not guarantee immediate memory zeroing. The credentials may persist in the heap until GC collection. |
| **Mitigation:** | Close the application immediately after use. For true memory-safe zeroing, a lower-level language (Rust/C) implementation is required. |
| **Log Truncation** | The Hash-Chain ensures the integrity of intermediate logs. However, without a signed genesis block, it cannot mathematically prevent root truncation (an attacker deleting the oldest entries and replacing the genesis `prev_hash` with zeros). |
| **Backup Permissions (Windows)** | The POSIX implementation restricts backup files to `0o600` (owner read/write). On Windows, equivalent ACL restrictions are not automatically applied, meaning local backups might be readable by other users on the same machine. |


## 🛠️ Technical Specifications

<details>
<summary><b>Click to expand Encryption Details</b></summary>

- **Core Algorithm:** AES-256-GCM (Authenticated Encryption)
- **Key Derivation Function (KDF):** Argon2id
- **Salt:** 16 bytes (randomly generated per vault)
- **Nonce/IV:** 12 bytes (unique per encryption cycle)
- **Key Length:** 256-bit for AES / 128-bit for Secret Key
</details>

<details>
<summary><b>System Requirements</b></summary>

- **Python Version:** 3.10 or higher
- **Dependencies:** 
  - `cryptography` (Engine)
  - `argon2-cffi` (Hashing)
  - `pyperclip` (Secure Clipboard)
  - `colorama` (Terminal UI)
  - `requests` (HIBP API integration)
</details>

## 🤖 CI/CD & Quality Assurance

This project leverages GitHub Actions to ensure stability:

- **Unit Tests**: Verifies key generator integrity.

- **Security Linting**: Static analysis via Bandit to detect potential vulnerabilities.

- **Build Pipeline**: Automated artifact generation.

## Important: Migration Notice

If you are upgrading from v1.0/v1.1, please note that the database format has changed for security reasons.

- Delete your old vault.hpro.

- Launch v1.6.0 to generate a new vault with the updated crypto engine.

- Import your passwords using option [5].

## 📜 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is provided "as is", without warranty of any kind. The user is solely responsible for the custody of their Master Password and Secret Key. If both are lost, your data is mathematically unrecoverable.

---

Developed by alvarofdezr