# Harpocrates Vault v1.0
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Security: Argon2id](https://img.shields.io/badge/Security-Argon2id-red)](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

**Harpocrates** is a high-security, local-first password manager named after the Greek god of silence and secrets. It implements a **Zero-Knowledge** architecture to ensure that your data remains private even if the storage medium is compromised.

## 🛡️ Security Architecture

Harpocrates goes beyond standard security by implementing a dual-factor key derivation process:

1.  **Key Derivation:** Uses **Argon2id** (Winner of the Password Hashing Competition).
    * `Memory Cost`: 64MB
    * `Time Cost`: 4 iterations
    * `Parallelism`: 4 threads
2.  **Dual-Entropy:** Requires both a **Master Password** and a 128-bit **Secret Key**.
3.  **Authenticated Encryption:** **AES-256-GCM** (Galois/Counter Mode) to ensure both confidentiality and integrity (tamper-proof).
4.  **Local-First:** No data ever leaves your machine in plaintext.

## ✨ Key Features

- ✅ **Secure Search:** Filter credentials instantly without compromising the encrypted source.
- ✅ **Entropy-Rich Generator:** Cryptographically secure password generation using `secrets`.
- ✅ **Binary Vault:** Custom `.hpro` format with automatic Salt and Nonce rotation.
- ✅ **Memory Sanitation:** Basic GC-based RAM wiping after session closure.

## 🚀 Installation & Usage

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

3. **Workflow:**
* First Run: Enter a Master Password. The system will generate your Secret Key. SAVE IT OFFLINE.
* Subsequent Access: Both credentials will be required to decrypt the vault.

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

## ⚠️ Disclaimer

This project is for educational purposes in the field of cybersecurity. Use at your own risk.

---

Developed with 🛡️ by alvarofdezr