<p align="center">
  <img src="img/icono.png" width="250" alt="Harpocrates Logo">
</p>

---

# 🔐 Harpocrates Vault v2.0
> **Zero-Knowledge Password Manager | Argon2id + AES-256-GCM**
![Security Status](https://github.com/alvarofdezrTU_/Harpocrates/actions/workflows/security-test.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shie2ds.io/badge/License-MIT-green)
![Release](https://img.shields.io/badge/Release-v1.2.0-purple)

**Harpocrates** is a robust Command Line Interface (CLI) password manager built for maximum security and privacy. It features a **Zero-Knowledge** architecture, meaning the application never stores or knows your master password; it is only used to derive encryption keys in volatile memory.

---
## 🚀 What's New in v1.2.0
- **Universal Import:** Seamlessly migrate passwords from **Bitwarden** or **Google Chrome** (.csv exports).
- **Automated Auditing:** Integrated CI/CD pipeline with GitHub Actions and `Bandit` security linting.
- **Extended Storage:** Support for Notes, URLs, and TOTP recovery codes.
- **Crypto Engine v1.2:** Hardened implementation with strict Salt/Nonce binding.

---

## 🛡️ Security Architecture

Security is not an afterthought; it's the core. Harpocrates uses industry-standard cryptography, avoiding "security by obscurity."

| Component | Technology | Description |
|-----------|------------|-------------|
| **KDF** (Key Derivation) | **Argon2id** | Memory-hard function resistant to GPU/ASIC brute-force attacks (OWASP Recommended). |
| **Encryption** | **AES-256-GCM** | Authenticated Encryption (AEAD). Ensures both confidentiality and integrity. |
| **RNG** | `os.urandom` | CSPRNG (Cryptographically Secure Pseudo-Random Number Generator). |
| **Memory** | **Volatile** | Keys are decrypted only in RAM and cleared upon exit. |

---

## 🚀 Installation & Usage

### Option A: Binary (Windows)
No Python required. Plug and play.
1. Go to [Releases](../../releases).
2. Download the latest `Harpocrates.exe`.
3. Run it from your terminal or CMD.

### Option B: From Source (Developers)
1. **Clone and Setup:**
   ```bash
   git clone [https://github.com/alvarofdezr/Harpocrates.git](https://github.com/alvarofdezr/Harpocrates.git)
   cd Harpocrates
   python -m venv venv
   # Activate venv
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
        ---------------------------------------------------------------------------------------
            ARCHITECTURE: Zero-Knowledge | ALGORITHMS: Argon2id + AES-256-GCM (v1.2)
        ---------------------------------------------------------------------------------------

    [?] Master Password: 
    [?] Secret Key: 

    [✓] Access Granted: Vault decrypted in memory.

    ----------------------------- MENÚ PRINCIPAL ------------------------------ 
    [1] List     -> View all accounts and securely copy passwords.
    [2] Add      -> Store a new credential (includes real-time strength meter).
    [3] Search   -> Deep search by service name or username.
    [4] Generate -> Create high-entropy passwords (32 chars).
    [5] Import   -> Batch import from CSV (Bitwarden/Chrome).
    [6] Exit     -> Clears memory buffers and closes the application.

    Harpocrates >
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
| **Memory Dump** | Harpocrates uses local variables and minimizes long-term RAM storage of sensitive keys (Work in Progress). |


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

- **Python Version:** 3.8 or higher
- **Dependencies:** - `cryptography` (Engine)
  - `argon2-cffi` (Hashing)
  - `python-dotenv` (Configuration)
  - `pyperclip` (Secure Clipboard)
</details>

## 🤖 CI/CD & Quality Assurance

This project leverages GitHub Actions to ensure stability:

- **Unit Tests**: Verifies key generator integrity.

- **Security Linting**: Static analysis via Bandit to detect potential vulnerabilities.

- **Build Pipeline**: Automated artifact generation.

## Important: Migration Notice

If you are upgrading from v1.0/v1.1, please note that the database format has changed for security reasons.

- Delete your old vault.hpro.

- Launch v1.2.0 to generate a new vault with the updated crypto engine.
d
- Import your passwords using option [5].

## 📜 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is provided "as is", without warranty of any kind. The user is solely responsible for the custody of their Master Password and Secret Key. If both are lost, your data is mathematically unrecoverable.

---

Developed by alvarofdezr