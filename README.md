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

**Harpocrates** is a robust Command Line Interface (CLI) password manager built for maximum security and privacy.

## 🚀 What's New in v2.0.0 (Vault Schema & Security Update)

This major release introduces **Format v2**, addressing the final theoretical vulnerabilities regarding audit log integrity:

**🛡️ Security & Core Architecture**
* **Signed Genesis Block:** Defeated the "Root Truncation" attack by signing the initial log entry via cryptographic HMAC tied to your ephemeral session key.
* **Format Decoupling:** `vault_format` and `app_version` are now logically separated.
* **Automatic Migrations:** Added seamless migration from v1.x databases directly through the core loader.


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
            ARCHITECTURE: Local Encrypted Vault | ALGORITHMS: Argon2id + AES-256-GCM (v1.2.0)
    ------------------------------------------------------------------------------------------

    [?] Master Password: 
    [?] Secret Key: 

    [✓] Access Granted: Vault decrypted in memory.

    ----------------------------- Main Menu (v1.2.0) ------------------------------ 
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
| **Memory Persistence** | Python's memory management (Garbage Collection) does not guarantee immediate zeroing of sensitive variables. **Mitigation:** Close the application immediately after use. |
| **Log Truncation** | **Mitigated in v2.0.0.** The standard hash-chain protects intermediate logs, and a Session-Key derived HMAC specifically protects the Genesis block against deletion. |
| **Backup Permissions (Windows)** | Windows ACL restrictions are not automatically applied, meaning local backups might be readable by other users. |


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
  - `zxcvbn` (Password Strength Estimation)
</details>

## 🤖 CI/CD & Quality Assurance

This project leverages GitHub Actions to ensure stability:

- **Unit Tests**: Verifies key generator integrity.

- **Security Linting**: Static analysis via Bandit to detect potential vulnerabilities.

- **Build Pipeline**: Automated artifact generation.

## Important: Migration Notice

If you are upgrading from v1.6.0, the format has changed to include cryptographic HMAC signatures for log integrity. 
* **You do not need to delete your vault.**
* When you launch v2.0.0 and enter your master credentials, the system will detect the old format and prompt you for automatic migration.

## 📜 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is provided "as is", without warranty of any kind. The user is solely responsible for the custody of their Master Password and Secret Key. If both are lost, your data is mathematically unrecoverable.

---

Developed by alvarofdezr