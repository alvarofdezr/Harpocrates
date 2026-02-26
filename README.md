<p align="center">
  <img src="img/icono.png" width="300" height="300" alt="Harpocrates Logo">
</p>

---
# 🔐 Harpocrates Vault v1.5.1
> **Zero-Knowledge Password Manager | Argon2id + AES-256-GCM**

![Security Status](https://github.com/alvarofdezr/Harpocrates/actions/workflows/security-test.yml/badge.svg?branch=main)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Release](https://img.shields.io/badge/Release-v1.5.1-blue)

**Harpocrates** is a robust Command Line Interface (CLI) password manager built for maximum security and privacy. It features a **Zero-Knowledge** architecture, meaning the application never stores or knows your master password.

## 🚀 What's New in v1.5.1 (Performance & Security Core Update)
> *"Focusing on what matters: Speed, Transparency, and Core Security."*

- **⚡ In-Memory Vault Caching:** Significant performance boost. The vault is now decrypted only once upon login and securely maintained in memory. Operations like searching, listing, and auditing are now instantaneous, eliminating redundant Argon2id CPU overhead and disk I/O.
- **🌍 Full English Standardization:** The entire CLI experience, internal forensic logs, and codebase have been unified into English for global consistency and a better professional user experience.
- **🎯 Strict Zero-Knowledge Focus:** Removed the experimental OSINT module to strictly adhere to the core Threat Model of a secure, offline, Zero-Knowledge password manager.
- **🛡️ Transparent Memory Management:** Removed misleading memory wiping variables to avoid a false sense of security. Updated the Threat Model documentation to provide an honest, technically accurate assessment of Python's runtime memory constraints.
- **🤖 CI/CD Pipeline Fixes:** Corrected Bandit static analysis configurations in GitHub Actions to ensure robust and accurate security vulnerability scanning on every commit.


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
    pip install -r requirements.txt  
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
            ARCHITECTURE: Zero-Knowledge | ALGORITHMS: Argon2id + AES-256-GCM (v1.5.1)
    ------------------------------------------------------------------------------------------

    [?] Master Password: 
    [?] Secret Key: 

    [✓] Access Granted: Vault decrypted in memory.

    ----------------------------- Main Menu (v1.5.1) ------------------------------ 
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

## 🔄 Data Flow (Zero-Knowledge)

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
| **Memory Dump** | As a Python application, master keys persist as immutable strings in RAM during the active session. Once the application is closed, memory references are deleted, but protection against live memory dumping (e.g., via specialized forensics or malware) is limited by the Python runtime environment. |


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

- Launch v1.5.1 to generate a new vault with the updated crypto engine.

- Import your passwords using option [5].

## 📜 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is provided "as is", without warranty of any kind. The user is solely responsible for the custody of their Master Password and Secret Key. If both are lost, your data is mathematically unrecoverable.

---

Developed by alvarofdezr