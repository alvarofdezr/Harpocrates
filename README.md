<p align="center">
  <img src="img/icono.png" width="300" height="300" alt="Harpocrates Logo">
</p>

---
# 🔐 Harpocrates Vault v2.0.0
> **Local Encrypted Vault Password Manager | Argon2id + AES-256-GCM**

![Security Status](https://github.com/alvarofdezr/Harpocrates/actions/workflows/security-test.yml/badge.svg?branch=main)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Release](https://img.shields.io/badge/Release-v2.0.0-blue)

**Harpocrates** is a local Command Line Interface (CLI) password manager designed to maximize security and privacy. It derives encryption keys locally and never stores the master key to disk.

## 🚀 What's New in v2.0.0

This release introduces a new vault schema and a complete architectural overhaul to meet senior-level security and engineering standards:

**🛡️ Security & Core Architecture**
* **Signed Genesis Block:** Defeats the "Root Truncation" attack by signing the initial log entry via cryptographic HMAC tied to the ephemeral session key.
* **Secure Memory Handling:** Replaces OS-level memory hacks with a cross-platform `SecureString` context manager. It stores passwords in mutable `bytearray` buffers and explicitly zeros the memory block upon exit.
* **Inactivity Auto-Lock:** A daemon thread monitors user activity and automatically locks the vault and terminates the process after 5 minutes of inactivity.
* **Format Decoupling & Migrations:** Logically separates `vault_format` from `app_version`. Seamlessly migrates v1.x databases directly through the core loader.

**🏗️ Code Quality & Infrastructure**
* **Command Dispatcher CLI:** Refactored the terminal interface to use a Command Dispatcher pattern, removing monolithic conditionals.
* **Configuration Management:** Abstracted cryptographic parameters (Argon2id costs) and paths into an environment-driven `Config` class.
* **100% Strict Type Checking:** The entire codebase enforces strict static typing, validated continuously via `mypy`.

## 🛡️ Security Architecture

Harpocrates relies on industry-standard cryptography:

| Component | Technology | Description |
|-----------|------------|-------------|
| **KDF** | **Argon2id** | Configured with 64MB RAM cost to resist GPU cracking farms (configurable via `.env`). |
| **Encryption** | **AES-256-GCM** | Authenticated Encryption (AEAD). Guarantees confidentiality and integrity. |
| **Audit** | **Encrypted Logs** | Event logs reside *inside* the encrypted blob. Only the owner reads the history. |
| **Privacy** | **K-Anonymity** | Uses SHA-1 prefixing (5 chars) to query breach databases (HaveIBeenPwned) anonymously. |

## 🚀 Installation & Usage

### Option A: Binary (Windows)
No Python required. Plug and play.
1. Go to [Releases](../../releases).
2. Download the latest `Harpocrates.exe`.
3. Run it from your terminal or CMD.

### Option B: From Source
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
3. **Usage:**
    Harpocrates will prompt for your Master Password and Secret Key. Once authenticated, it loads the vault into memory and presents the main menu.
    ```plaintext
    ----------------------------- Main Menu (v2.0.0) ------------------------------ 
    [1] List         -> View accounts. Select an ID to Copy Password, Edit, or Delete.
    [2] Search       -> Deep search by service name or username.
    [3] Add          -> Store a new credential (includes strength meter).
    [4] Generate     -> Create high-entropy passwords (32 chars).
    [5] Import       -> Batch import from CSV.
    [6] Backup       -> Create a timestamped copy of your vault.
    [7] Audit Log    -> Inspect the internal Forensic Event History.
    [8] HIBP Scan    -> Check your vault against 8 billion leaked passwords.
    [9] Exit         -> Clears session references and closes.
    ```

## 🚨 Security Testing
Verify the vault's resistance against brute-force attacks by running the simulation script:
```bash
python tests/attack_simulation.py
```
Run the full test suite (covering cryptography, in-memory caching, and data integrity):
```bash
python -m unittest discover tests
```

## 🔄 Data Flow

1. **Input:** User provides Master Password + Secret Key.
2. **Derivation:** Argon2id processes inputs with a unique Salt.
3. **Encryption:** AES-256-GCM encrypts the JSON vault.
4. **Storage:** Only the Salt, Nonce, and Ciphertext are written to `.hpro`.
5. **Security:** The Master Password and Keys are never stored on disk and are zeroed from memory immediately after use.

## 🔒 Threat Model & Mitigations

| Threat | Mitigation |
| :--- | :--- |
| **Brute Force (Online)** | Argon2id with high memory cost makes local cracking attempts computationally expensive. |
| **Vault Theft** | Even with the `.hpro` file, an attacker needs BOTH the Master Password and the 128-bit Secret Key. |
| **Data Tampering** | AES-GCM provides AEAD. Any modification to the encrypted file results in a decryption failure. |
| **Memory Persistence** | Python's garbage collection does not zero memory. **Mitigation:** Sensitive strings are stored in mutable `bytearray` buffers (`SecureString` context manager) and explicitly overwritten with zeros after use. |
| **Physical Terminal Access** | An attacker accesses the terminal while the vault is unlocked. **Mitigation:** An auto-lock daemon terminates the process after 5 minutes of inactivity. |
| **Log Truncation** | The standard hash-chain protects intermediate logs, and a Session-Key derived HMAC protects the Genesis block against deletion. |

## 🛠️ Technical Specifications

<details>
<summary><b>Encryption Details</b></summary>

- **Core Algorithm:** AES-256-GCM (Authenticated Encryption)
- **Key Derivation Function (KDF):** Argon2id
- **Salt:** 16 bytes (randomly generated per vault)
- **Nonce/IV:** 12 bytes (unique per encryption cycle)
- **Key Length:** 256-bit for AES / 128-bit for Secret Key
</details>

<details>
<summary><b>System Requirements</b></summary>

- **Python Version:** 3.10 or higher
- **Dependencies:** `cryptography`, `argon2-cffi`, `pyperclip`, `colorama`, `requests`, `zxcvbn`
</details>

## 🤖 CI/CD & Quality Assurance

This project leverages GitHub Actions to enforce strict engineering standards:

- **Unit Tests:** Verifies key generator and core vault integrity.
- **Security Linting:** Static analysis via `Bandit` and `pip-audit` detects potential vulnerabilities.
- **Static Typing:** Exhaustive type checking enforced via `mypy --strict`.
- **Formatting:** Code style enforced via `black` and `flake8`.

## 📜 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is provided "as is", without warranty of any kind. The user is solely responsible for the custody of their Master Password and Secret Key. If both are lost, the data is mathematically unrecoverable.

---

Developed by alvarofdezr