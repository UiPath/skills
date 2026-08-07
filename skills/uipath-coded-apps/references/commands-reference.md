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
| `--build-dir <dir>` | Build output directory | `dist` |
| `--ignore-resources` | Skip importing referenced resources | `false` |
| `--base-url <url>` | UiPath base URL | From `.env` |
| `--org-id <id>` | Organization ID | From `.env` |
| `--tenant-id <id>` | Tenant ID | From `.env` |
| `--access-token <token>` | Supported CLI override; agents must not pass or log tokens manually—use `--profile` | From `.env` |

**Examples:**

```bash
# Push using project ID from .env
uip codedapp push

# Push with explicit project ID
uip codedapp push my-project-id

# Push a custom build directory
uip codedapp push my-project-id --build-dir build

# Push without importing resources
uip codedapp push --ignore-resources
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
| `--target-dir <dir>` | Local directory to write pulled files | Current directory |
| `--base-url <url>` | UiPath base URL | From `.env` |
| `--org-id <id>` | Organization ID | From `.env` |
| `--tenant-id <id>` | Tenant ID | From `.env` |
| `--access-token <token>` | Supported CLI override; agents must not pass or log tokens manually—use `--profile` | From `.env` |

**Examples:**

```bash
# Pull using project ID from .env
uip codedapp pull

# Pull with explicit project ID
uip codedapp pull my-project-id

# Pull to a specific directory
uip codedapp pull my-project-id --target-dir ./my-app

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
| `--description <desc>` | Package description | Prompted |
| `--main-file <file>` | Main entry file | `index.html` |
| `--content-type <type>` | Content type: `webapp`, `library`, `process` | `webapp` |
| `--dry-run` | Preview packaging without creating the file | `false` |
| `--repository-url <url>` | Source repository recorded for traceability | None |
| `--repository-commit <sha>` | Source commit recorded for traceability | None |
| `--repository-branch <branch>` | Source branch recorded for traceability | None |
| `--repository-type <type>` | Repository type; defaults to `git` with a repository URL | None |
| `--release-notes <text>` | Package release notes | None |
| `--project-url <url>` | Automation Hub idea URL | None |
| `--profile <name>` | Named CLI profile; accepted as a global option but pack does not need cloud authentication | Active/default profile |

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
uip codedapp pack dist -n my-webapp --version 1.0.0 --author "My Team" --description "Production app" --main-file app.html
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
| `--personal-workspace` | Publish to the current user's Personal Workspace feed | Tenant feed |
| `--uipath-dir <dir>` | Directory containing `.nupkg` files | `./.uipath` |
| `--base-url <url>` | UiPath base URL | From `.env` |
| `--org-id <id>` | Organization ID | From `.env` |
| `--tenant-id <id>` | Tenant ID | From `.env` |
| `--tenant-name <name>` | Tenant name (required for registration) | From `.env` |
| `--access-token <token>` | Supported CLI override; agents must not pass or log tokens manually—use `--profile` | From `.env` |
| `--profile <name>` | Named authenticated CLI profile | Active/default profile |

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

Deploy or upgrade a coded app in UiPath. The CLI can auto-detect, but agents must choose and verify the intent before execution.

- **Create**: fresh remote inventory proves the deployment is absent and the exact route is unused; pass `--path-name`.
- **Upgrade**: fresh remote inventory proves the exact deployment, system name, route, current version, and candidate; omit `--path-name` and preserve the route.

App name is resolved from: `--name` flag → `.uipath/app.config.json` → interactive prompt. This resolution is convenience, not remote-state proof. Treat local config as a repairable hint and never let it decide create versus upgrade.

```bash
uip codedapp deploy [options]
```

| Option | Description | Default |
|--------|-------------|---------|
| `-n, --name <name>` | App name | From `.uipath/app.config.json` or prompted |
| `--path-name <name>` | Permanent hosted route; use only for a proven create | Tool default |
| `--client-id <id>` | Exact non-confidential OAuth client override | Tool/config default |
| `-v, --version <version>` | Exact **published** candidate to deploy (different semantic from `pack`/`publish` `-v`) | Latest |
| `--base-url <url>` | UiPath base URL | From `.env` |
| `--org-id <id>` | Organization ID | From `.env` |
| `--org-name <name>` | Organization name (used for app URL) | From `.env` |
| `--tenant-id <id>` | Tenant ID | From `.env` |
| `--folder-key <key>` | UiPath folder key | From `UIPATH_FOLDER_KEY` env var |
| `--access-token <token>` | Supported CLI override; agents must not pass or log tokens manually—use `--profile` | From `.env` |
| `--tags <tags>` | Comma-separated categorization labels | None |
| `--profile <name>` | Named authenticated CLI profile | Active/default profile |

**Examples:**

```bash
# Proven create: exact route is unused
uip codedapp deploy -n my-webapp --version 1.0.0 \
  --path-name my-webapp --client-id <client-guid> \
  --folder-key <folder-guid> --profile <profile> --output json

# Proven upgrade: preserve the route by omitting --path-name
uip codedapp deploy -n my-webapp --version 1.1.0 \
  --client-id <client-guid> --folder-key <folder-guid> \
  --profile <profile> --output json
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

### Deployment safety boundary

- Direct CLI deployment without a second approval is testing-only: explicit internal synthetic-data testing in Alpha or Staging, exact candidate/target binding, automatic receipt, and post-deploy verification.
- Production, customer data, or durable release evidence requires a governed plan and immutable receipt.
- A publish/deploy timeout, interruption, 5xx, HTML response, or nonzero exit is indeterminate until remote reconciliation. Never blind-retry, auto-bump, randomize or omit the route, delete/recreate, or fall back from upgrade to create.

---

## Common Options

Cloud commands expose these target/authentication overrides (availability varies by subcommand; prefer an exact named profile):

| Option | Description |
|--------|-------------|
| `--base-url <url>` | UiPath base URL |
| `--org-id <id>` | Organization ID |
| `--tenant-id <id>` | Tenant ID |
| `--access-token <token>` | Supported CLI override, but agents must not pass or log tokens manually; use `--profile` |
| `--profile <name>` | Named authenticated CLI profile |
