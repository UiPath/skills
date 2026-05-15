# Pack / Publish / Deploy Guide

Complete guide for packaging, publishing, and deploying UiPath Coded Web Applications to production.

## Pipeline Overview

```
Build → Pack → Publish → Deploy
  │       │        │         │
  │       │        │         └── Deploy or upgrade the app in UiPath
  │       │        └── Upload .nupkg to Orchestrator + register the app
  │       └── Package build output into .nupkg with UiPath metadata
  └── Build the web application (npm run build)
```

Each step depends on the previous one:
- **Pack** needs the `dist/` directory (from build)
- **Publish** needs the `.nupkg` file (from pack)
- **Deploy** needs the app registration (from publish)

## Pack

Package the app build output into a `.nupkg` file with UiPath metadata.

### Basic Usage

```bash
# Pack with interactive prompts
uip codedapp pack dist

# Pack with all options specified
uip codedapp pack dist -n my-webapp --version 1.0.0 -a "My Team" --description "Production app"
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `<dist>` | Path to build output directory | **Required** |
| `-n, --name <name>` | Package name | Prompted |
| `-v, --version <version>` | Package version | `1.0.0` |
| `-o, --output <dir>` | Output directory for `.nupkg` | `./.uipath` |
| `-a, --author <author>` | Package author | `UiPath Developer` |
| `--description <desc>` | Package description | Prompted |
| `--main-file <file>` | Main entry file | `index.html` |
| `--content-type <type>` | `webapp`, `library`, or `process` | `webapp` |
| `--dry-run` | Preview without creating | `false` |
| `--reuse-client` | Reuse clientId from `uipath.json` | `false` |

### Content Types

| Type | Use Case |
|------|----------|
| `webapp` | Standard web application with UI (default) |
| `library` | Reusable component library consumed by other apps |
| `process` | Process-driven application without standalone UI |

### Generated Metadata

The `.nupkg` includes auto-generated UiPath metadata files:

| File | Purpose |
|------|---------|
| `operate.json` | Runtime configuration and app settings |
| `bindings.json` | Resource bindings for connections, assets |
| `bindings_v2.json` | V2 resource bindings format |
| `entry-points.json` | API entry point definitions |
| `package-descriptor.json` | Package file mapping and manifest |

### OAuth Client ID

Pack manages the `uipath.json` SDK config file, which includes the OAuth client ID for the deployed app:
- First pack: creates a new non-confidential client ID
- Subsequent packs: use `--reuse-client` to keep the existing client ID from `uipath.json`

### Dry Run

Preview what would be packaged without creating the file:

```bash
uip codedapp pack dist --dry-run
```

### Output

```
Package Details:
  Name: my-webapp
  Version: 1.0.0
  Type: webapp
  Location: ./.uipath/my-webapp.1.0.0.nupkg
```

---

## Publish

Upload the `.nupkg` to UiPath Orchestrator and register the coded app with the Apps service in a single step.

### Basic Usage

```bash
# Auto-select if only one .nupkg exists
uip codedapp publish

# Select specific package
uip codedapp publish -n my-webapp --version 1.0.0
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-n, --name <name>` | Package name (skip interactive selection) | Auto or prompted |
| `-v, --version <version>` | Package version (requires `--name`) | Latest |
| `-t, --type <type>` | App type: `Web` or `Action` | `Web` |
| `--uipath-dir <dir>` | Directory containing `.nupkg` files | `./.uipath` |

### App Types

| Type | Description |
|------|-------------|
| `Web` | Standard web app accessible via browser URL (default) |
| `Action` | Action app triggered by UiPath automation workflows |

### What Happens Internally

1. Selects the `.nupkg` file (auto-select, by name, or interactive)
2. Uploads the package to Orchestrator via the OData API
3. Registers the coded app with the UiPath Apps service
4. Creates `.uipath/app.config.json` with registration metadata

### App Config File

After publish, `.uipath/app.config.json` stores the registration:

```json
{
  "appName": "my-webapp",
  "appVersion": "1.0.0",
  "systemName": "my-webapp_abc123",
  "appUrl": null,
  "registeredAt": "2025-02-26T10:00:00.000Z",
  "appType": "Web",
  "deploymentId": null,
  "deployedAt": null
}
```

This file is consumed by `deploy` to resolve the app name automatically. **Do not delete `.uipath/` between publish and deploy.**

### Multiple Packages

If multiple `.nupkg` files exist in `.uipath/`, the command will prompt for selection unless `--name` is provided:

```bash
# Select by name (skips prompt)
uip codedapp publish -n my-webapp

# Select specific version
uip codedapp publish -n my-webapp --version 2.0.0
```

---

## Deploy

Deploy or upgrade a coded app in UiPath. The command auto-detects whether to perform a fresh deployment or upgrade an existing one.

### Basic Usage

```bash
# Deploy (uses app.config.json)
uip codedapp deploy

# Deploy with explicit name
uip codedapp deploy -n my-webapp
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-n, --name <name>` | App name | From `app.config.json` or prompted |
| `-v, --version <version>` | Target a **specific published version** to deploy (different semantic from `pack`/`publish`'s `-v`, which is the package version) | Latest |
| `--folder-key <key>` | UiPath folder **key** (GUID, not the name). **Always pass explicitly** — see below. | From `UIPATH_FOLDER_KEY` env var, else interactive (avoid) |
| `--org-name <name>` | Organization name (for app URL) | From `.env` |

### Fresh Deploy vs. Upgrade

| Scenario | Behavior |
|----------|----------|
| **First deploy** | Deploys version 1 of the app |
| **Already deployed** | Upgrades to the latest published version |

The command resolves the app name from:
1. `--name` flag (highest priority)
2. `.uipath/app.config.json` (created by `publish`)
3. Interactive prompt (fallback)

### Folder Key

The `deploy` command requires a folder **key** (GUID), not a folder name. Users typically know the folder name only — resolve the key via `uip or folders list` before calling `deploy`.

Resolution order:
1. `--folder-key <key>` flag — explicit, idiomatic
2. `UIPATH_FOLDER_KEY=<key>` env-var prefix — equivalent to the flag, useful in CI/CD where the value is already in env
3. Interactive folder selection (**must avoid** — see warning below)

> **Pass the folder key explicitly via the flag or env var.** Running `uip codedapp deploy` with neither drops the command into an interactive folder picker that fails in non-TTY contexts (CI, agent shells, IDE terminals piped to a runner). When invoked from an agent, you MUST resolve the key up-front and pass it.

#### Resolving folder name → folder key

When the user provides a folder **name** (e.g., `"Shared"`), resolve it to a key with `uip or folders list --output json` and match on the `Name` field (or `Path` for nested paths).

> **Prerequisite:** `uip or ...` commands require the Orchestrator tool. Run `uip tools list` first; if `orchestrator-tool` is missing, install it once: `uip tools install @uipath/orchestrator-tool`.

```bash
# 0. Ensure the Orchestrator tool is installed (idempotent — skip if already present)
uip tools list --output json | grep -q '"orchestrator-tool"' || uip tools install @uipath/orchestrator-tool

# 1. List folders the current user has access to (includes Personal, Solution, Standard)
uip or folders list --output json > /tmp/folders.json

# 2. Resolve "Shared" → key (GUID)
FOLDER_KEY=$(python3 -c "
import json
with open('/tmp/folders.json') as f:
    d = json.load(f)
match = next((x for x in d['Data'] if x['Name'] == 'Shared'), None)
print(match['Key'] if match else '')
")

# 3. Deploy with the resolved key
uip codedapp deploy -n my-webapp --folder-key "$FOLDER_KEY"
```

If the name is ambiguous (multiple matches) or not found, surface an error to the user — do NOT fall through to interactive selection.

`uip or folders list` returns folders the **current user** has access to (personal workspaces, solution folders, and standard folders). Add `--all` if you need every folder in the tenant — but for `deploy` resolution, the default view is what you want.

Each folder JSON object includes: `Key` (GUID — pass this to `--folder-key`), `Name`, `Path`, `Description`, `Type` (`Personal` / `Solution` / `Standard`), `ParentKey`.

#### Storing the resolved key

```bash
# Persist for re-use across deploys
echo "UIPATH_FOLDER_KEY=$FOLDER_KEY" >> .env
```

### Output

**Fresh deploy:**
```
  App Name: my-webapp
  Version: 1.0.0
  App URL: https://cloud.uipath.com/myorg/apps_/my-webapp
```

**Upgrade:**
```
  App Name: my-webapp
  Version: 2.0.0
  App URL: https://cloud.uipath.com/myorg/apps_/my-webapp
```

---

## Full Pipeline Examples

### First-Time Deployment

```bash
# 1. Authenticate
uip login

# 2. Build the app
npm run build

# 3. Pack
uip codedapp pack dist -n my-webapp

# 4. Publish
uip codedapp publish

# 5. Deploy
uip codedapp deploy
```

### Version Update

```bash
# 1. Make changes and rebuild
npm run build

# 2. Pack with bumped version
uip codedapp pack dist -n my-webapp --version 2.0.0

# 3. Publish new version
uip codedapp publish

# 4. Deploy (auto-detects upgrade)
uip codedapp deploy
```

### CI/CD Pipeline

```bash
# Non-interactive flow with explicit options — every flag passed, no prompts
uip login --client-id $CLIENT_ID --client-secret $CLIENT_SECRET
npm run build
uip codedapp pack dist -n my-webapp --version $VERSION
uip codedapp publish -n my-webapp --version $VERSION
uip codedapp deploy -n my-webapp --folder-key $FOLDER_KEY
```

### Agent flow (user provides folder name only)

```bash
# 1. Resolve folder name → key
FOLDER_KEY=$(uip or folders list --output json \
  | python3 -c "import json,sys;d=json.load(sys.stdin);m=next((x for x in d['Data'] if x['Name']=='$USER_FOLDER_NAME'),None);print(m['Key'] if m else '')")

[ -z "$FOLDER_KEY" ] && { echo "Folder '$USER_FOLDER_NAME' not found"; exit 1; }

# 2. Deploy non-interactively with the resolved key
uip codedapp deploy -n my-webapp --folder-key "$FOLDER_KEY"
```

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `No packages found` | Missing `.nupkg` | Run `uip codedapp pack` first |
| `Version already exists` | Same version published | Bump version: `-v 2.0.0` |
| `App not found` on deploy | App not published | Run `uip codedapp publish` first |
| `Folder key required` / deploy hangs on prompt | Missing folder key | Resolve via `uip or folders list --output json`, then run `uip codedapp deploy --folder-key <key> ...` (or `UIPATH_FOLDER_KEY=<key>` env-var prefix). |
| `Missing tenant name` on publish | `UIPATH_TENANT_NAME` not set | Set in `.env` or pass `--tenant-name` |
| `dist/ not found` | App not built | Run `npm run build` |
| Pack shows wrong clientId | Stale `uipath.json` | Use `--reuse-client` or delete `uipath.json` |
