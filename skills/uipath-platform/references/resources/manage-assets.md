# Manage Assets

Create configuration assets, share them across folders, and manage credential rotation.

> For full option details on any command, use `--help` (e.g., `uip resource assets create --help`).

## When to Use

- Setting up environment configuration (API URLs, feature flags, retry counts)
- Managing secrets and credentials used by automations at runtime
- Sharing configuration across multiple folders/teams
- Rotating credentials without redeploying processes

## Prerequisites

- Authenticated (`uip login`)
- Target folder exists (see [setup-environment.md](../orchestrator/setup-environment.md))
- For Credential/Secret types: a credential store must exist (`uip or credential-stores list`)

## Flow

```mermaid
graph LR
    A[assets create] --> B[assets list]
    B --> C[assets get]
    B --> D[assets get-asset-value]
    A --> E[assets share]
    E --> F[assets get-folders]
    F --> G[assets unshare]
    A --> H[assets update]
    H --> I[assets delete]
```

---

## Step 1: Create Assets

Create a named configuration value in a folder. Type defaults to Text.

```bash
uip resource assets create "ApiBaseUrl" "https://api.example.com" \
  --folder-path "Finance" --type Text --output json

uip resource assets create "MaxRetries" "3" \
  --folder-path "Finance" --type Integer --output json

uip resource assets create "FeatureEnabled" "true" \
  --folder-path "Finance" --type Bool --output json
```

Key options:

| Option | Description |
|--------|-------------|
| `--type <type>` | `Text` (default), `Bool`, `Integer`, `Credential`, `Secret` |
| `--scope <scope>` | `Global` (default) or `PerRobot` |
| `--description <text>` | Human-readable description |
| `--tags <csv>` | Comma-separated tag names |
| `--has-default` | Asset has a default value (default: true) |
| `--credential-store-key <key>` | Required for Credential and Secret types |

For Credential and Secret types, you must provide `--credential-store-key`:

```bash
uip resource assets create "DbPassword" "s3cret-value" \
  --folder-path "Finance" --type Secret \
  --credential-store-key <store-key> --output json

uip resource assets create "ServiceAccount" "svc-user:p@ssw0rd" \
  --folder-path "Finance" --type Credential \
  --credential-store-key <store-key> --output json
```

## Step 2: List Assets

List assets in a folder. Requires `--folder-path` or `--folder-key`.

```bash
uip resource assets list --folder-path "Finance" --output json

# Filter by name (contains match)
uip resource assets list --folder-path "Finance" --name "Api" --output json

# Filter by type
uip resource assets list --folder-path "Finance" --type Secret --output json
```

## Step 3: Get Asset Details

Get full asset metadata by key. Cross-folder -- no `--folder-path` needed.

```bash
uip resource assets get <asset-key> --output json
```

**Note:** Credential and secret values are NOT returned by `get`. Use `get-asset-value` to retrieve decrypted values.

## Step 4: Get Asset Value

Returns the decrypted asset value for the current user. Requires `--folder-path` or `--folder-key`.

```bash
uip resource assets get-asset-value <asset-key> \
  --folder-path "Finance" --output json
```

This is the only way to retrieve credential/secret values from the CLI. The response includes the resolved value based on the current user's context (relevant for PerRobot-scoped assets).

## Step 5: Update Asset

Update an existing asset's value, type, scope, or metadata. Cross-folder -- no `--folder-path` needed.

```bash
# Update value
uip resource assets update <asset-key> "https://api-v2.example.com" --output json

# Update description and tags
uip resource assets update <asset-key> --description "Updated endpoint" \
  --tags "production,api" --output json

# Change scope
uip resource assets update <asset-key> --scope PerRobot --output json
```

Only provided fields are changed -- omitted fields keep their current values.

## Step 6: Share Asset with Another Folder

Make an asset accessible in an additional folder:

```bash
uip resource assets share <asset-key> --folder-path "Production" --output json
```

## Step 7: Check Where Shared

List all folders where the asset is currently accessible:

```bash
uip resource assets get-folders <asset-key> --output json
```

Returns `accessibleFolders` (array of folders you can see) and `totalFoldersCount` (total, including folders you lack permission to view).

## Step 8: Unshare

Remove the asset from a folder:

```bash
uip resource assets unshare <asset-key> --folder-path "Production" --output json
```

## Step 9: Delete

Delete the asset entirely. Cross-folder -- no `--folder-path` needed.

```bash
uip resource assets delete <asset-key> --output json
```

---

## Credential Rotation Pattern

Rotate a secret without downtime:

```bash
# 1. Create the replacement secret
uip resource assets create "DbPassword-v2" "new-s3cret" \
  --folder-path "Finance" --type Secret \
  --credential-store-key <store-key> --output json

# 2. Share with all folders that use it
uip resource assets share <new-key> --folder-path "Production" --output json

# 3. Update consuming processes to reference the new asset name
#    (or update the original asset in-place if the name must stay the same)
uip resource assets update <original-key> "new-s3cret" --output json

# 4. Verify the new value resolves correctly
uip resource assets get-asset-value <asset-key> \
  --folder-path "Finance" --output json

# 5. Delete the old version (if you created a new asset instead of updating)
uip resource assets delete <old-key> --output json
```

---

## Complete Example

Set up environment configuration for a Finance folder with text, integer, and secret assets, then share the secret with Production:

```bash
# Create text asset
uip resource assets create "ApiBaseUrl" "https://api.example.com" \
  --folder-path "Finance" --type Text \
  --description "Production API endpoint" --output json

# Create integer asset
uip resource assets create "MaxRetries" "5" \
  --folder-path "Finance" --type Integer \
  --description "Maximum retry attempts" --output json

# Create secret asset (requires credential store)
uip resource assets create "ApiKey" "sk-prod-abc123" \
  --folder-path "Finance" --type Secret \
  --credential-store-key <store-key> \
  --description "Production API key" --output json

# Share secret with Production folder
uip resource assets share <api-key-asset-key> \
  --folder-path "Production" --output json

# Verify sharing
uip resource assets get-folders <api-key-asset-key> --output json

# Confirm value is accessible from Production
uip resource assets get-asset-value <api-key-asset-key> \
  --folder-path "Production" --output json
```

---

## Variations and Gotchas

### Credential format

Credential type assets require `username:password` format. The colon separates the username from the password:

```bash
uip resource assets create "WinCred" "DOMAIN\\user:p@ssw0rd" \
  --folder-path "Finance" --type Credential \
  --credential-store-key <store-key> --output json
```

### `get` does NOT return credential/secret values

`assets get` returns metadata only -- credential and secret values are redacted for security. Use `assets get-asset-value` to retrieve the actual decrypted value.

### Cross-folder vs folder-scoped commands

| Command | Folder required? |
|---------|-----------------|
| `list` | Yes (`--folder-path` or `--folder-key`) |
| `create` | Yes |
| `get-asset-value` | Yes |
| `get` | No (cross-folder) |
| `update` | No (cross-folder) |
| `delete` | No (cross-folder) |
| `get-folders` | No (cross-folder) |
| `share` | Yes (target folder via `--folder-path` or `--folder-key`) |
| `unshare` | Yes (target folder via `--folder-path` or `--folder-key`) |

### `--credential-store-key` is required for Credential and Secret types

If you omit it, the command fails with an explicit error. Use `uip or credential-stores list --output json` to find the key.

### Bool values must be literal `true` or `false`

Case-insensitive, but no other truthy/falsy values are accepted (not `1`, `0`, `yes`, `no`).

### Integer must be a whole number

Decimals and non-numeric strings are rejected.

---

## Related

- [resources.md](resources.md) -- Overview of all resource commands
- [setup-environment.md](../orchestrator/setup-environment.md) -- Create folders before creating assets
