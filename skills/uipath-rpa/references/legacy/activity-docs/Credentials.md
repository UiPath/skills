# UiPath Credentials Activities - Community Reference

## Overview
Windows Credential Manager integration for storing/retrieving credentials. Package: `UiPath.Credentials.Activities` (from Community.Activities repo).

---

## Activities

| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `GetSecureCredential` | Get credential (SecureString password) | Target (required), CredentialType, PersistanceType -> Username (string), Password (SecureString) |
| `GetCredential` | Get credential (plain string password) | Target (required), CredentialType, PersistanceType -> Username, Password (string) |
| `AddCredential` | Store new credential | Target (required), Username, Password/SecurePassword, CredentialType, PersistanceType |
| `DeleteCredential` | Remove stored credential | Target (required), CredentialType, PersistanceType |
| `RequestCredential` | Prompt user for credentials | Target -> Username, Password/SecurePassword |

---

## Enums

### CredentialType
- `Generic` (default) - Generic credential
- `DomainPassword` - Domain/Windows credential
- `DomainCertificate` - Certificate-based

### PersistanceType (note spelling)
- `Session` - Current login session only
- `LocalComputer` - Machine-level persistence
- `Enterprise` (default) - Domain/roaming profile

---

## Critical Gotchas

1. **GetSecureCredential preferred over GetCredential** - returns SecureString instead of plain text password
2. **Target is the credential name/key** in Windows Credential Manager - must match exactly
3. **PersistanceType spelled "Persistance"** (typo in codebase, not "Persistence") - use as-is
4. **Enterprise persistence** roams with domain profile - available on any domain-joined machine
5. **Session persistence** lost on logout - temporary storage only
6. **RequestCredential shows Windows credential dialog** - blocks workflow until user responds
7. **Windows Credential Manager only** - not cross-platform (Windows desktop only)
8. **GetCredential returns Result (bool)** - true if credential found, false if not
9. **DeleteCredential silently succeeds** if credential doesn't exist
10. **Credential names are case-insensitive** in Windows Credential Manager
