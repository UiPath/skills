# UiPath Cryptography Activities - Community Reference

## Overview
Encryption, decryption, hashing, and PGP operations. Package: `UiPath.Cryptography.Activities` (from Community.Activities repo).

---

## Activities

### Symmetric Encryption
| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `EncryptFile` | Encrypt file with symmetric key | InputFilePath, OutputFilePath, Key/SecureKey, Algorithm, Encoding (default UTF-8) |
| `DecryptFile` | Decrypt file with symmetric key | InputFilePath, OutputFilePath, Key/SecureKey, Algorithm, Encoding |
| `EncryptText` | Encrypt text string | Input (string), Key/SecureKey, Algorithm, Encoding -> Result (string) |
| `DecryptText` | Decrypt text string | Input (string), Key/SecureKey, Algorithm, Encoding -> Result (string) |

### Hashing (HMAC)
| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `KeyedHashFile` | HMAC hash of file | InputFilePath, Key/SecureKey, Algorithm, Encoding -> Result (string, hex) |
| `KeyedHashText` | HMAC hash of text | Input (string), Key/SecureKey, Algorithm, Encoding -> Result (string, hex) |

### PGP (Pretty Good Privacy)
| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `PgpSignFile` | Sign file with PGP private key | InputFilePath, OutputFilePath, PrivateKeyFilePath, PrivateKeyPassphrase, Armor |
| `PgpClearSignFile` | Clear-sign file (readable + signature) | InputFilePath, OutputFilePath, PrivateKeyFilePath, PrivateKeyPassphrase |
| `PgpVerify` | Verify PGP signature | InputFilePath, PublicKeyFilePath -> IsAuthentic (bool) |
| `PgpGenerateKeyPair` | Generate PGP key pair | Identity, Passphrase, PublicKeyFilePath, PrivateKeyFilePath, KeyLength, ExpirationDate |

---

## Encryption Algorithms
- AES (default, recommended)
- DES (legacy, weak)
- RC2 (legacy)
- Rijndael (AES variant)
- TripleDES (3DES, legacy)

## Hash Algorithms (for HMAC)
- HMACSHA256 (default, recommended)
- HMACSHA384
- HMACSHA512
- HMACMD5 (weak, avoid)
- HMACRIPEMD160

---

## Critical Gotchas

### Key Management
1. **Key/SecureKey are overload groups** - provide one or the other, not both
2. **SecureKey (SecureString) recommended** over plaintext Key for security
3. **Key is used as password for key derivation** - not used directly as encryption key
4. **Encoding must match between encrypt and decrypt** - default UTF-8

### Algorithm Selection
5. **Use AES** for new implementations - DES/RC2/3DES are legacy and weak
6. **DES key is only 56 bits** - trivially breakable by modern standards
7. **AES-256 is the default** and recommended choice

### File Operations
8. **InputFilePath and OutputFilePath cannot be the same** for file encryption/decryption
9. **Output file is overwritten** if it exists
10. **Large files processed in memory** - may cause OutOfMemoryException for very large files

### PGP
11. **PGP key files must be in standard OpenPGP format** (.asc for ASCII-armored, .pgp/.gpg for binary)
12. **Armor=true produces ASCII output** (text-safe); false produces binary
13. **PgpVerify returns IsAuthentic=false** (not exception) for invalid signatures
14. **PgpGenerateKeyPair KeyLength** options: 1024 (weak), 2048 (minimum), 4096 (recommended)
15. **ExpirationDate** - null means key never expires

### Hashing
16. **Hash results are hex-encoded strings** (lowercase)
17. **HMAC requires a key** - unlike simple hashing, HMAC provides authentication
18. **HMACMD5 is cryptographically weak** - use HMACSHA256+ for security

### Encoding
19. **Encoding parameter** defaults to UTF-8 but must match across encrypt/decrypt
20. **Binary files should use appropriate encoding** or base64 wrapper
