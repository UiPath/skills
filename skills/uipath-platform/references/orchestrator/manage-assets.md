# Manage Assets

Create configuration assets, share them across folders, and manage credential rotation.

For command details, run `uip or assets <command> --help` (for example, `uip or assets create --help`).

## When to Use

- Set API URLs, feature flags, retry counts, and other environment configuration.
- Manage runtime secrets and credentials.
- Share configuration across folders or teams.
- Rotate credentials without redeploying processes.

## Prerequisites

- Run `uip login status`. If not logged in, ask the user to run `uip login` (it opens an interactive browser flow).
- Ensure the target folder exists (see [setup-environment.md](setup-environment.md)).
- For `Credential` and `Secret` assets, run `uip or credential-stores list` and ensure a credential store exists.

Create, list, inspect, retrieve, update, share, inspect sharing, unshare, and delete assets as needed.

## Step 1: Create Assets

Run `assets create` with a folder path. The type defaults to `Text`:

```bash
uip or assets create "ApiBaseUrl" "https://api.example.com" --folder-path "Finance" --type Text --output json
uip or assets create "MaxRetries" "3" --folder-path "Finance" --type Integer --output json
uip or assets create "FeatureEnabled" "true" --folder-path "Finance" --type Bool --output json
```

Supported options:

| Option | Description |
|---|---|
| `--type <type>` | `Text` (default), `Bool`, `Integer`, `Credential`, or `Secret` |
| `--scope <scope>` | `Global` (default) or `PerRobot` |
| `--description <text>` | Human-readable description |
| `--tags <csv>` | Comma-separated tag names |
| `--has-default` | Asset has a default value (default: true) |
| `--credential-store-key <key>` | Required for `Credential` and `Secret` |

For credential or secret assets, run:

```bash
uip or assets create "DbPassword" "s3cret-value" --folder-path "Finance" --type Secret --credential-store-key <store-key> --output json
uip or assets create "ServiceAccount" "svc-user:p@ssw0rd" --folder-path "Finance" --type Credential --credential-store-key <store-key> --output json
```

## Step 2: List Assets

Run `assets list` with `--folder-path` or `--folder-key`, or run it with `--all-folders`:

```bash
uip or assets list --folder-path "Finance" --output json
uip or assets list --folder-path "Finance" --name "Api" --output json
uip or assets list --folder-path "Finance" --type Secret --output json
uip or assets list --all-folders --output json
```

If the user provides a folder name or path, pass it directly as `--folder-path`; do not run `uip or folders list` merely to validate it. If `assets list --name ... --folder-path ... --output json` shows the asset is absent, stop.

## Step 3: Get Asset Details

Run this cross-folder command without `--folder-path`:

```bash
uip or assets get <asset-key> --output json
```

`Credential` and `Secret` values are not returned by `get`.

## Step 4: Get Asset Value

Run this command with `--folder-path` or `--folder-key` to retrieve the decrypted value:

```bash
uip or assets get-asset-value <asset-key> --folder-path "Finance" --output json
```

This is the only CLI method for retrieving credential or secret values. The response resolves the value for the current user, including `PerRobot` context.

## Step 5: Update Asset

Run `update` without `--folder-path`; it is cross-folder. Only supplied fields change:

```bash
uip or assets update <asset-key> "https://api-v2.example.com" --output json
uip or assets update <asset-key> --description "Updated endpoint" --tags "production,api" --output json
uip or assets update <asset-key> --scope PerRobot --output json
```

## Step 6: Share Asset with Another Folder

Run:

```bash
uip or assets share <asset-key> --folder-path "Production" --output json
```

## Step 7: Check Where Shared

Run this cross-folder command:

```bash
uip or assets get-folders <asset-key> --output json
```

The response includes `accessibleFolders` (folders you can see) and `totalFoldersCount` (all folders, including those you cannot view).

## Step 8: Unshare

Run this command with the target folder:

```bash
uip or assets unshare <asset-key> --folder-path "Production" --output json
```

## Step 9: Delete

Run this cross-folder command:

```bash
uip or assets delete <asset-key> --yes --output json
```

## Credential Rotation Pattern

Rotate without downtime:

```bash
# 1. Create the replacement secret
uip or assets create "DbPassword-v2" "new-s3cret" --folder-path "Finance" --type Secret --credential-store-key <store-key> --output json

# 2. Share it with every consuming folder
uip or assets share <new-key> --folder-path "Production" --output json

# 3. Update consumers to use the new asset name, or update the original in place
uip or assets update <original-key> "new-s3cret" --output json

# 4. Verify resolution
uip or assets get-asset-value <asset-key> --folder-path "Finance" --output json

# 5. If a new asset replaced the old one, delete the old version
uip or assets delete <old-key> --yes --output json
```

## Variations and Gotchas

### Credential format

`Credential` values require `username:password`; the colon separates the username and password:

```bash
uip or assets create "WinCred" "DOMAIN\\user:p@ssw0rd" --folder-path "Finance" --type Credential --credential-store-key <store-key> --output json
```

### Secret-value retrieval

`assets get` returns metadata only and redacts credential and secret values. Run `assets get-asset-value` to retrieve the decrypted value.

### Cross-folder versus folder-scoped commands

| Command | Folder required? |
|---|---|
| `list` | Yes (`--folder-path` or `--folder-key`), or `--all-folders` |
| `create` | Yes |
| `get-asset-value` | Yes (`--folder-path` or `--folder-key`) |
| `get` | No (cross-folder) |
| `update` | No (cross-folder) |
| `delete` | No (cross-folder) |
| `get-folders` | No (cross-folder) |
| `share` | Yes, target folder via `--folder-path` or `--folder-key` |
| `unshare` | Yes, target folder via `--folder-path` or `--folder-key` |

### Validation

- `--credential-store-key` is required for `Credential` and `Secret`. Run `uip or credential-stores list --output json` to find the key.
- `Bool` values must be literal `true` or `false` (case-insensitive); `1`, `0`, `yes`, and `no` are rejected.
- `Integer` values must be whole numbers; decimals and non-numeric strings are rejected.

## Related

- [resources.md](resources.md) -- Overview of all resource commands
- [setup-environment.md](setup-environment.md) -- Create folders before creating assets