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
uip codedapp pack dist -n my-webapp -v 1.0.0 -a "My Team" --description "Production app"
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
uip codedapp publish -n my-webapp -v 1.0.0
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-n, --name <name>` | Package name (skip interactive selection) | Auto or prompted |
| `-v, --version <version>` | Package version (requires `--name`) | Latest |
| `-t, --type <type>` | App type: `Web` or `Action` | `Web` |
| `--uipathDir <dir>` | Directory containing `.nupkg` files | `./.uipath` |

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
uip codedapp publish -n my-webapp -v 2.0.0
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
| `--folderKey <key>` | UiPath folder key | From `UIPATH_FOLDER_KEY` env var |
| `--orgName <name>` | Organization name (for app URL) | From `.env` |

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

The `deploy` command requires a folder key, resolved from:
1. `--folderKey` flag
2. `UIPATH_FOLDER_KEY` environment variable
3. Interactive folder selection (if neither is set)

Set it during auth or manually:
```bash
# Set in .env
echo "UIPATH_FOLDER_KEY=my-folder-key" >> .env

# Or pass directly
uip codedapp deploy --folderKey my-folder-key
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
uip codedapp pack dist -n my-webapp -v 2.0.0

# 3. Publish new version
uip codedapp publish

# 4. Deploy (auto-detects upgrade)
uip codedapp deploy
```

### CI/CD Pipeline

```bash
# Non-interactive flow with explicit options
uip login --clientId $CLIENT_ID --clientSecret $CLIENT_SECRET
npm run build
uip codedapp pack dist -n my-webapp -v $VERSION
uip codedapp publish -n my-webapp -v $VERSION
uip codedapp deploy -n my-webapp --folderKey $FOLDER_KEY
```

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `No packages found` | Missing `.nupkg` | Run `uip codedapp pack` first |
| `Version already exists` | Same version published | Bump version: `-v 2.0.0` |
| `App not found` on deploy | App not published | Run `uip codedapp publish` first |
| `Folder key required` | Missing `UIPATH_FOLDER_KEY` | Set in `.env` or pass `--folderKey` |
| `Missing tenant name` on publish | `UIPATH_TENANT_NAME` not set | Set in `.env` or pass `--tenantName` |
| `dist/ not found` | App not built | Run `npm run build` |
| Pack shows wrong clientId | Stale `uipath.json` | Use `--reuse-client` or delete `uipath.json` |
