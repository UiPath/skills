# Coded App CLI Command Reference

Complete reference for all `uip codedapp` subcommands.

<!--skill-flavor:host-scope:start-->
<!--skill-flavor:host-scope:end-->
## Prerequisites

- **Authentication**: Run `uip login` before using cloud commands (auth is handled by the `uip` CLI, not the codedapp tool)
- **Installation**: `uip tools install @uipath/codedapp-tool`
- **Command prefix**: All commands are under `uip codedapp <command>`

## `uip codedapp push`

Push local source code to Studio Web. Uploads the build output directory and optionally imports referenced resources.

If no project ID is provided, the command prompts to create a new Studio Web solution with a Coded App project inside it, or to use an existing solution. For a new solution it asks for the solution name and the project name, both defaulting to the current folder name. Pass `--solution-name` and `--project-name` to create the solution without prompts, which you must do when you cannot answer prompts. The new `UIPATH_PROJECT_ID` is saved to `.env`.

The two name flags only apply when no project ID is set. If one is set by `--project-id`, `UIPATH_PROJECT_ID`, or `.env`, push fails instead of pushing into that project.

```bash
uip codedapp push [options]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--project-id <id>` | WebApp Project ID | From `UIPATH_PROJECT_ID` env var or `.env` |
| `--solution-name <name>` | Name of the Studio Web solution to create when no project ID is set | Prompted |
| `--project-name <name>` | Name of the Coded App project to create when no project ID is set | Prompted |
| `--build-dir <dir>` | Build output directory | `dist` |
| `--ignore-resources` | Skip importing referenced resources | `false` |
| `--base-url <url>` | UiPath base URL | From `uip login` session |
| `--org-id <id>` | Organization ID | From `uip login` session |
| `--tenant-id <id>` | Tenant ID | From `uip login` session |
| `--access-token <token>` | Access token | From `uip login` session |

**Examples:**

```bash
# Push using project ID from .env
uip codedapp push

# Push with explicit project ID
uip codedapp push --project-id <project-id>

# Push a custom build directory
uip codedapp push --project-id <project-id> --build-dir build

# Push without importing resources
uip codedapp push --ignore-resources

# First push: create a named solution and project without prompts
uip codedapp push --solution-name "Product Announcements" --project-name "Announcements Portal"
```

**Auto-create project flow:**
```
? No project ID found. Would you like to create a new solution or use an existing one? Create a new solution
? Enter a name for the new solution (the Studio Web container for your app and its resources): Product Announcements
? Enter a name for the new Coded App (the app end users open): Announcements Portal
✔ Created solution "Product Announcements" with coded app project "Announcements Portal" (ID: abc-123-def)
  Saved UIPATH_PROJECT_ID to .env
```

**API endpoints:**
- Push files: `POST /{org}/studio_/backend/api/Project/{projectId}/FileOperations`
- Create project: `POST /{org}/studio_/backend/api/Solution`

---

## `uip codedapp pull`

Pull project files from Studio Web to your local machine.

```bash
uip codedapp pull [options]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--project-id <id>` | WebApp Project ID | From `UIPATH_PROJECT_ID` env var or `.env` |
| `--overwrite` | Allow overwriting existing local files without prompting | `false` |
| `--target-dir <dir>` | Local directory to write pulled files | Current directory |
| `--base-url <url>` | UiPath base URL | From `uip login` session |
| `--org-id <id>` | Organization ID | From `uip login` session |
| `--tenant-id <id>` | Tenant ID | From `uip login` session |
| `--access-token <token>` | Access token | From `uip login` session |

**Examples:**

```bash
# Pull using project ID from .env
uip codedapp pull

# Pull with explicit project ID
uip codedapp pull --project-id <project-id>

# Pull to a specific directory
uip codedapp pull --project-id <project-id> --target-dir ./my-app

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
| `--author <author>` | Package author | `UiPath Developer` |
| `--description <text>` | Package description | Prompted |
| `--main-file <file>` | Main entry file | `index.html` |
| `--content-type <type>` | Content type: `webapp`, `library`, `process` | `webapp` |
| `--dry-run` | Preview packaging without creating the file | `false` |
| `--base-url <url>` | UiPath base URL | From `uip login` session |
| `--org-id <id>` | Organization ID | From `uip login` session |
| `--tenant-id <id>` | Tenant ID | From `uip login` session |
| `--access-token <token>` | Access token | From `uip login` session |

**Examples:**

```bash
# Pack the dist directory (interactive prompts for name)
uip codedapp pack dist

# Pack with explicit name and version
uip codedapp pack dist -n my-webapp --version 2.0.0

# Pack to a custom output directory
uip codedapp pack dist -o ./packages

# Preview packaging without creating the file
uip codedapp pack dist --dry-run

# Pack with all options
uip codedapp pack dist -n my-webapp --version 1.0.0 -a "My Team" --description "Production app" --main-file app.html
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
| `-v, --version <version>` | Package version (requires `--name`). Selects the **first** matching `.nupkg` in unsorted `readdir` order — NOT the highest version. Always pass when multiple versions of the same name sit in `.uipath/`. | First name match |
| `-t, --type <type>` | App type: `Web` or `Action` | `Web` |
| `--uipath-dir <dir>` | Directory containing `.nupkg` files | `./.uipath` |
| `--base-url <url>` | UiPath base URL | From `uip login` session |
| `--org-id <id>` | Organization ID | From `uip login` session |
| `--tenant-id <id>` | Tenant ID | From `uip login` session |
| `--tenant-name <name>` | Tenant name (required for registration) | From `uip login` session |
| `--access-token <token>` | Access token | From `uip login` session |

**Examples:**

```bash
# Publish (auto-selects if only one .nupkg exists)
uip codedapp publish

# Publish a specific package by name
uip codedapp publish -n my-webapp

# Publish a specific version
uip codedapp publish -n my-webapp --version 2.0.0

# Publish as an Action app type
uip codedapp publish -t Action

# Publish from a custom directory
uip codedapp publish --uipath-dir ./packages
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
| `-v, --version <version>` | Target a specific **published** version (different semantic from `pack`/`publish` `-v`, which is the package version) | Latest |
| `--path-name <slug>` | URL slug (routing name). First deploy sets it (defaults to sanitized app name); on upgrade, **omit to keep the URL** — re-passing a taken or previously-used slug fails with `routing name must be unique` | Sanitized app name |
| `--base-url <url>` | UiPath base URL | From `uip login` session |
| `--org-id <id>` | Organization ID | From `uip login` session |
| `--org-name <name>` | Organization name (used for app URL) | From `uip login` session |
| `--tenant-id <id>` | Tenant ID | From `uip login` session |
| `--folder-key <key>` | UiPath folder key | From `UIPATH_FOLDER_KEY` env var |
| `--access-token <token>` | Access token | From `uip login` session |

**Examples:**

```bash
# Deploy (uses app name from .uipath/app.config.json)
uip codedapp deploy

# Deploy with explicit app name
uip codedapp deploy -n my-webapp

# Deploy with folder key
uip codedapp deploy -n my-webapp --folder-key my-folder-key

# Same deploy, key via env var — skips the --folder-key pre-check (incomplete folder lookup on accounts with very many folders)
UIPATH_FOLDER_KEY=my-folder-key uip codedapp deploy -n my-webapp
```

> `--folder-key` pre-checks the key against one unpaged copy of the account's folder list, which is incomplete on accounts with very many folders. If it reports an existing folder as `not found among folders accessible to your account`, use the env-var form — see [pack-publish-deploy.md](pack-publish-deploy.md#deploy-rejects-a-valid-folder-key-as-not-found-among-folders-accessible).

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

Cloud commands resolve base URL, org, tenant, and access token from your `uip login` session automatically (any login type) — you don't pass them. Pass the corresponding flag only to override a session value.

| Option | Description |
|--------|-------------|
| `--base-url <url>` | UiPath base URL (from `uip login` session) |
| `--org-id <id>` | Organization ID (from `uip login` session) |
| `--tenant-id <id>` | Tenant ID (from `uip login` session) |
| `--access-token <token>` | Access token (from `uip login` session) |
