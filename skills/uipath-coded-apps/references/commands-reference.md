# Coded App CLI Command Reference

Complete reference for all `uip codedapp` subcommands.

## Prerequisites

- **Authentication**: Run `uip login` before using cloud commands (auth is handled by the `uip` CLI, not the codedapp tool)
- **Installation**: `uip tools install @uipath/codedapp-tool`
- **Command prefix**: All commands are under `uip codedapp <command>`

## `uip codedapp push`

Push local source code to Studio Web. Uploads the build output directory and optionally imports referenced resources.

If no project ID is provided, the command **interactively prompts** to create a new Coded App project. The newly created `UIPATH_PROJECT_ID` is saved to `.env`.

```bash
uip codedapp push [project-id] [options]
```

| Option | Description | Default |
|--------|-------------|---------|
| `[project-id]` | WebApp Project ID | From `UIPATH_PROJECT_ID` env var |
| `--buildDir <dir>` | Build output directory | `dist` |
| `--ignoreResources` | Skip importing referenced resources | `false` |
| `--baseUrl <url>` | UiPath base URL | From `.env` |
| `--orgId <id>` | Organization ID | From `.env` |
| `--tenantId <id>` | Tenant ID | From `.env` |
| `--accessToken <token>` | Access token | From `.env` |

**Examples:**

```bash
# Push using project ID from .env
uip codedapp push

# Push with explicit project ID
uip codedapp push my-project-id

# Push a custom build directory
uip codedapp push my-project-id --buildDir build

# Push without importing resources
uip codedapp push --ignoreResources
```

**Auto-create project flow:**
```
? No project ID found. Create a new Coded App project? (Y/n)
? Enter a name for the new Coded App: my-webapp
✔ Created coded app project "my-webapp" with ID: abc-123-def
  Saved UIPATH_PROJECT_ID to .env
```

**API endpoints:**
- Push files: `POST /{org}/studio_/backend/api/Project/{projectId}/FileOperations`
- Create project: `POST /{org}/studio_/backend/api/Solution`

---

## `uip codedapp pull`

Pull project files from Studio Web to your local machine.

```bash
uip codedapp pull [project-id] [options]
```

| Option | Description | Default |
|--------|-------------|---------|
| `[project-id]` | WebApp Project ID | From `UIPATH_PROJECT_ID` env var |
| `--overwrite` | Allow overwriting existing local files without prompting | `false` |
| `--targetDir <dir>` | Local directory to write pulled files | Current directory |
| `--baseUrl <url>` | UiPath base URL | From `.env` |
| `--orgId <id>` | Organization ID | From `.env` |
| `--tenantId <id>` | Tenant ID | From `.env` |
| `--accessToken <token>` | Access token | From `.env` |

**Examples:**

```bash
# Pull using project ID from .env
uip codedapp pull

# Pull with explicit project ID
uip codedapp pull my-project-id

# Pull to a specific directory
uip codedapp pull my-project-id --targetDir ./my-app

# Pull and overwrite without prompting
uip codedapp pull --overwrite
```

**API endpoint:** `GET /{org}/studio_/backend/api/Project/{projectId}/FileOperations`

---

## `uip codedapp pack`

Package the app build output into a `.nupkg` file for publishing. Generates all required UiPath metadata files and bundles them with app content.

```bash
uip codedapp pack <dist> [options]
```

| Option | Description | Default |
|--------|-------------|---------|
| `<dist>` | Path to build output directory | **Required** |
| `-n, --name <name>` | Package name | Prompted interactively |
| `-v, --version <version>` | Package version | `1.0.0` |
| `-o, --output <dir>` | Output directory for `.nupkg` | `./.uipath` |
| `-a, --author <author>` | Package author | `UiPath Developer` |
| `--description <desc>` | Package description | Prompted |
| `--main-file <file>` | Main entry file | `index.html` |
| `--content-type <type>` | Content type: `webapp`, `library`, `process` | `webapp` |
| `--dry-run` | Preview packaging without creating the file | `false` |
| `--reuse-client` | Reuse existing clientId from uipath.json | `false` |
| `--baseUrl <url>` | UiPath base URL | From `.env` |
| `--orgId <id>` | Organization ID | From `.env` |
| `--tenantId <id>` | Tenant ID | From `.env` |
| `--accessToken <token>` | Access token | From `.env` |

**Examples:**

```bash
# Pack the dist directory (interactive prompts for name)
uip codedapp pack dist

# Pack with explicit name and version
uip codedapp pack dist -n my-webapp -v 2.0.0

# Pack to a custom output directory
uip codedapp pack dist -o ./packages

# Preview packaging without creating the file
uip codedapp pack dist --dry-run

# Pack with all options
uip codedapp pack dist -n my-webapp -v 1.0.0 -a "My Team" --description "Production app" --main-file app.html
```

**Output:**
```
Package Details:
  Name: my-webapp
  Version: 1.0.0
  Type: webapp
  Location: ./.uipath/my-webapp.1.0.0.nupkg
```

**Generated metadata files** (inside `.nupkg`):
- `operate.json` — Runtime configuration
- `bindings.json` / `bindings_v2.json` — Resource bindings
- `entry-points.json` — API entry point definitions
- `package-descriptor.json` — Package file mapping

---

## `uip codedapp publish`

Publish a `.nupkg` to UiPath Orchestrator **and** register the coded app with the Apps service. Combines upload and registration into a single step.

```bash
uip codedapp publish [options]
```

| Option | Description | Default |
|--------|-------------|---------|
| `-n, --name <name>` | Package name (non-interactive selection) | Auto-select or prompted |
| `-v, --version <version>` | Package version (requires `--name`) | Latest |
| `-t, --type <type>` | App type: `Web` or `Action` | `Web` |
| `--uipathDir <dir>` | Directory containing `.nupkg` files | `./.uipath` |
| `--baseUrl <url>` | UiPath base URL | From `.env` |
| `--orgId <id>` | Organization ID | From `.env` |
| `--tenantId <id>` | Tenant ID | From `.env` |
| `--tenantName <name>` | Tenant name (required for registration) | From `.env` |
| `--accessToken <token>` | Access token | From `.env` |

**Examples:**

```bash
# Publish (auto-selects if only one .nupkg exists)
uip codedapp publish

# Publish a specific package by name
uip codedapp publish -n my-webapp

# Publish a specific version
uip codedapp publish -n my-webapp -v 2.0.0

# Publish as an Action app type
uip codedapp publish -t Action

# Publish from a custom directory
uip codedapp publish --uipathDir ./packages
```

**Output:**
```
✔ Package uploaded successfully
✔ Coded app registered successfully

Published App Details:
  Name: my-webapp
  Version: 1.0.0
  System Name: my-webapp_abc123
```

**Side effect:** Creates `.uipath/app.config.json` with registration metadata.

**API endpoints:**
- Upload: `POST /{org}/{tenant}/orchestrator_/odata/Processes/UiPath.Server.Configuration.OData.UploadPackage()`
- Register: `POST /{org}/apps_/default/api/v1/default/models/apps/codedapp/publish`

---

## `uip codedapp deploy`

Deploy or upgrade a coded app in UiPath. Automatically detects whether to perform a fresh deployment or upgrade.

- **Fresh deploy**: App has not been deployed before → deploys version 1
- **Upgrade**: App is already deployed → upgrades to the latest published version

App name is resolved from: `--name` flag → `.uipath/app.config.json` → interactive prompt.

```bash
uip codedapp deploy [options]
```

| Option | Description | Default |
|--------|-------------|---------|
| `-n, --name <name>` | App name | From `.uipath/app.config.json` or prompted |
| `--baseUrl <url>` | UiPath base URL | From `.env` |
| `--orgId <id>` | Organization ID | From `.env` |
| `--orgName <name>` | Organization name (used for app URL) | From `.env` |
| `--tenantId <id>` | Tenant ID | From `.env` |
| `--folderKey <key>` | UiPath folder key | From `UIPATH_FOLDER_KEY` env var |
| `--accessToken <token>` | Access token | From `.env` |

**Examples:**

```bash
# Deploy (uses app name from .uipath/app.config.json)
uip codedapp deploy

# Deploy with explicit app name
uip codedapp deploy -n my-webapp

# Deploy with folder key
uip codedapp deploy -n my-webapp --folderKey my-folder-key
```

**Fresh deploy output:**
```
  App Name: my-webapp
  Version: 1.0.0
  App URL: https://cloud.uipath.com/myorg/apps_/my-webapp
```

**Upgrade output:**
```
  App Name: my-webapp
  Version: 2.0.0
  App URL: https://cloud.uipath.com/myorg/apps_/my-webapp
```

**API endpoints:**
- New deploy: `POST /{org}/apps_/default/api/v1/default/models/{systemName}/publish/versions/1/deploy`
- Upgrade: `POST /{org}/apps_/default/api/v1/default/models/deployed/apps/updateToLatestAppVersionBulk`

---

## Common Options

All cloud commands accept these override options (values default to `.env` file):

| Option | Description |
|--------|-------------|
| `--baseUrl <url>` | UiPath base URL |
| `--orgId <id>` | Organization ID |
| `--tenantId <id>` | Tenant ID |
| `--accessToken <token>` | Access token |
