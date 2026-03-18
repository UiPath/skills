# Assets

Orchestrator assets — key-value pairs for externalizing configuration so the same automation package works across environments.

> **Concepts and types** are documented in [../orchestrator/orchestrator-guide.md - Assets](../orchestrator/orchestrator-guide.md). This file covers the `resources` CLI commands for asset management.

## CLI Commands

> **Note:** Assets are currently accessible via both `uip or assets` (orchestrator-tool) and `uip resources assets` (resources-tool). The `resources` commands below are the unified interface going forward.

### List Assets

```bash
uip resources assets list --folder-id <folder-id> --format json
```

With OData filter:
```bash
uip resources assets list --folder-id <folder-id> --filter "Name eq 'ApiKey'" --format json
```

### Get Asset

```bash
uip resources assets get --folder-id <folder-id> --name "ApiKey" --format json
```

### Create Asset

```bash
# Text asset (default type)
uip resources assets create --folder-id <folder-id> --name "ApiBaseUrl" --value "https://api.example.com" --format json

# Secret asset
uip resources assets create --folder-id <folder-id> --name "ApiKey" --value "sk-abc123" --type Secret --format json

# Integer asset
uip resources assets create --folder-id <folder-id> --name "MaxRetries" --value "3" --type Integer --format json

# Credential asset (username:password format)
uip resources assets create --folder-id <folder-id> --name "ServiceAccount" --value "user:password" --type Credential --format json
```

### Update Asset

```bash
uip resources assets update --folder-id <folder-id> --name "ApiBaseUrl" --value "https://api-v2.example.com" --format json
```

### Delete Asset

```bash
uip resources assets delete --folder-id <folder-id> --asset-id <asset-id> --format json
```

## Asset Types

| Type | Value Format | Example |
|---|---|---|
| Text | Plain string | `"https://api.example.com"` |
| Secret | Encrypted string | `"sk-abc123"` |
| Integer | Numeric string | `"3"` |
| Bool | `"true"` / `"false"` | `"true"` |
| Credential | `"username:password"` | `"svc_user:p@ssw0rd"` |
| DBConnectionString | Connection string | `"Server=...;Database=..."` |
| HttpConnectionString | URL | `"https://api.example.com"` |
| WindowsCredential | `"domain\\user:password"` | `"CORP\\svc_user:p@ssw0rd"` |

## Asset Scope

| Scope | Behavior |
|---|---|
| **Global** | Same value for all robots in the folder |
| **PerRobot** | Different value per robot (allows overrides) |
