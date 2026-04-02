---
name: uipath-coded-apps
description: "End-to-end toolkit for UiPath Coded Web Applications: authenticate, push/pull source code to Studio Web, package into .nupkg, publish to Orchestrator, and deploy. TRIGGER when: User wants to create, build, push, pull, pack, publish, or deploy a UiPath coded web app; User mentions coded apps, coded web apps, codedapp, web application in a UiPath context; User asks about pushing code to Studio Web, packaging a web app, publishing a .nupkg, deploying a coded app; User asks about uip codedapp CLI commands, .uipath directory, app.config.json, or coded app project lifecycle. DO NOT TRIGGER when: User is working with coded agents (Python — use uipath-coded-agents instead); User is working with coded workflows (.cs files — use uipath-coded-workflows instead); User is working with XAML/RPA workflows (use uipath-rpa-workflows instead); User asks about Orchestrator management without coded app context (use uipath-platform instead)."
metadata:
   allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Coded Apps

Comprehensive guide for building, syncing, packaging, publishing, and deploying UiPath Coded Web Applications using the `uip codedapp` CLI.

## When to Use This Skill

- User wants to **push local code to Studio Web** or **pull code from Studio Web**
- User wants to **package a web app** into a `.nupkg` for Orchestrator
- User wants to **publish a coded app** to Orchestrator and register it
- User wants to **deploy or upgrade** a coded app in UiPath
- User wants to run the **full pipeline** (build → pack → publish → deploy)
- User asks about `uip codedapp` commands, `.uipath/` directory, or `app.config.json`
- User wants to **sync files** between local development and Studio Web

## Critical Rules

- **Always check login status before any cloud command.** Run `uip login status --output json` first. If not authenticated, ask the user for their environment and run `uip login`.
- **Never skip the build step.** The `dist/` directory must exist before `pack` or `push`. Always verify with `ls dist/`.
- **Pack before publish, publish before deploy.** The commands form a pipeline — each step depends on the previous one producing its output.
- **The `publish` command creates `app.config.json`.** This file is used by `deploy` to resolve the app name. Don't delete `.uipath/` between publish and deploy.
- **Push auto-creates projects.** If no `UIPATH_PROJECT_ID` exists, `push` will interactively prompt to create a new Coded App project and save the ID to `.env`.
- **Version must be bumped for re-publish.** If the same version already exists in Orchestrator, publish will fail. Bump the version in the `pack` step.

## Lifecycle Stages

| Stage | Description | CLI Command |
|-------|-------------|-------------|
| **Auth** | Authenticate with UiPath Cloud | `uip login` |
| **Build** | Build the web application | `npm run build` (or project-specific) |
| **Push** | Upload source code to Studio Web | `uip codedapp push [project-id]` |
| **Pull** | Download project files from Studio Web | `uip codedapp pull [project-id]` |
| **Pack** | Package build output into `.nupkg` | `uip codedapp pack <dist>` |
| **Publish** | Upload to Orchestrator + register app | `uip codedapp publish` |
| **Deploy** | Deploy or upgrade app in UiPath | `uip codedapp deploy` |

## Quick Start

### Step 0 — Resolve the `uip` binary

The `uip` CLI is installed via npm. If `uip` is not on PATH, resolve it first:

```bash
UIP=$(command -v uip 2>/dev/null || npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip
$UIP --version
```

Use `$UIP` in place of `uip` for all subsequent commands if the plain `uip` command isn't found.

### Step 1 — Authenticate

```bash
uip login status --output json
```

If not logged in:

```bash
uip login                                          # interactive OAuth (opens browser)
uip login --authority https://alpha.uipath.com     # non-production environments
```

### Step 2 — Choose your workflow

| I want to... | Go to |
|---|---|
| **Sync code with Studio Web** (push/pull) | [File Sync](#file-sync) |
| **Package and deploy to production** (pack/publish/deploy) | [Ship It](#ship-it-full-pipeline) |
| **Just package for testing** | [Pack](#pack) |

## Task Navigation

| I need to... | Read these |
|---|---|
| **Push code to Studio Web** | [references/file-sync.md](references/file-sync.md) |
| **Pull code from Studio Web** | [references/file-sync.md](references/file-sync.md) |
| **Package app into .nupkg** | [references/pack-publish-deploy.md](references/pack-publish-deploy.md) |
| **Publish to Orchestrator** | [references/pack-publish-deploy.md](references/pack-publish-deploy.md) |
| **Deploy or upgrade an app** | [references/pack-publish-deploy.md](references/pack-publish-deploy.md) |
| **Full CLI command reference** | [references/commands-reference.md](references/commands-reference.md) |
| **Manage Orchestrator resources** | [/uipath:uipath-platform](/uipath:uipath-platform) |

---

## File Sync

Sync source code between local development and UiPath Studio Web using `push` and `pull`.

### Push — Upload Local Code to Studio Web

```bash
# Push using project ID from .env
uip codedapp push

# Push with explicit project ID
uip codedapp push my-project-id

# Push a custom build directory
uip codedapp push --buildDir build

# Push without importing resources
uip codedapp push --ignoreResources
```

If no `UIPATH_PROJECT_ID` exists, the command auto-creates a new Coded App project interactively and saves the ID to `.env`.

### Pull — Download Files from Studio Web

```bash
# Pull using project ID from .env
uip codedapp pull

# Pull to a specific directory
uip codedapp pull my-project-id --targetDir ./my-app

# Pull and overwrite without prompting
uip codedapp pull --overwrite
```

### File Sync Workflow

**First-time push (new project):**
```bash
npm run build
uip codedapp push
# → Prompts to create project, saves UIPATH_PROJECT_ID to .env
```

**Ongoing development:**
```bash
# Push local changes to Studio Web
uip codedapp push

# Pull remote changes to local
uip codedapp pull
```

**Reference:** [File Sync Guide](references/file-sync.md) — Push/pull commands, auto-project creation, conflict handling, common workflows.

---

## Pack

Package the app build output into a `.nupkg` file with UiPath metadata.

```bash
# Pack the dist directory
uip codedapp pack dist

# Pack with explicit name and version
uip codedapp pack dist -n my-webapp -v 2.0.0

# Preview packaging without creating the file
uip codedapp pack dist --dry-run
```

The pack command generates UiPath metadata files inside the `.nupkg`: `operate.json`, `bindings.json`, `entry-points.json`, and `package-descriptor.json`.

**Reference:** [Pack / Publish / Deploy Guide](references/pack-publish-deploy.md) — All pack options, content types, metadata files.

---

## Publish

Upload the `.nupkg` to Orchestrator and register the coded app with the Apps service.

```bash
# Publish (auto-selects if only one .nupkg exists)
uip codedapp publish

# Publish a specific package
uip codedapp publish -n my-webapp -v 2.0.0

# Publish as an Action app type
uip codedapp publish -t Action
```

Creates `.uipath/app.config.json` with registration metadata used by `deploy`.

**Reference:** [Pack / Publish / Deploy Guide](references/pack-publish-deploy.md) — Publish options, app types, app.config.json.

---

## Deploy

Deploy or upgrade a coded app in UiPath. Auto-detects fresh deploy vs. upgrade.

```bash
# Deploy (uses app name from .uipath/app.config.json)
uip codedapp deploy

# Deploy with explicit app name
uip codedapp deploy -n my-webapp

# Deploy with folder key
uip codedapp deploy -n my-webapp --folderKey my-folder-key
```

**Reference:** [Pack / Publish / Deploy Guide](references/pack-publish-deploy.md) — Deploy options, fresh vs upgrade, folder key.

---

## Ship It (Full Pipeline)

Run the complete pipeline end-to-end: build → pack → publish → deploy.

**IMPORTANT: Do NOT stop between steps to ask "would you like me to continue?". Execute the entire flow automatically. Only pause when you genuinely need information from the user (auth credentials, app name). After getting that info, resume immediately.**

1. **Auth** — Check `uip login status --output json`. If not logged in, ask the user for their environment (Production/Alpha/Staging) and run `uip login`.

2. **Build** — Run the project's build command:
   ```bash
   npm run build
   ```
   Verify: `ls dist/` (or the custom build directory).

3. **Pack** — Package the build output:
   ```bash
   uip codedapp pack dist -n <name> -v <version>
   ```
   If a previous version exists in `.uipath/app.config.json`, suggest bumping the version. Verify: `ls .uipath/*.nupkg`.

4. **Publish** — Upload and register:
   ```bash
   uip codedapp publish
   ```
   Verify: `cat .uipath/app.config.json`.

5. **Deploy** — Deploy or upgrade:
   ```bash
   uip codedapp deploy
   ```
   Share the App URL from the output with the user.

**Update cycle (version bump):**
```bash
npm run build
uip codedapp pack dist -n my-webapp -v 2.0.0
uip codedapp publish
uip codedapp deploy
```

---

## Key Concepts

### Environment Variables

The tool reads credentials from `.env` (created by `uip login` or `uip login`):

| Variable | Used By | Description |
|----------|---------|-------------|
| `UIPATH_ACCESS_TOKEN` | All commands | Bearer token for API calls |
| `UIPATH_URL` / `UIPATH_BASE_URL` | All commands | UiPath Cloud base URL |
| `UIPATH_ORGANIZATION_ID` | All commands | Organization ID |
| `UIPATH_ORGANIZATION_NAME` | deploy | Organization name (for app URL) |
| `UIPATH_TENANT_ID` | All commands | Tenant ID |
| `UIPATH_TENANT_NAME` | publish | Tenant name |
| `UIPATH_FOLDER_KEY` | deploy | Folder key |
| `UIPATH_PROJECT_ID` | push, pull | Studio Web project ID |

### App Configuration (`.uipath/app.config.json`)

Created by `publish`, consumed by `deploy`:

```json
{
  "appName": "my-webapp",
  "appVersion": "1.0.0",
  "systemName": "my-webapp_abc123",
  "appUrl": null,
  "registeredAt": "2025-02-26T10:00:00.000Z",
  "appType": "Web",
  "deploymentId": "dep-xyz",
  "deployedAt": "2025-02-26T10:05:00.000Z"
}
```

### Content Types

| Type | Description |
|------|-------------|
| `webapp` | Standard web application (default) |
| `library` | Reusable UI component library |
| `process` | Process-driven application |

### App Types

| Type | Description |
|------|-------------|
| `Web` | Standard web app (default) |
| `Action` | Action app triggered by automation |

---

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `Not authenticated` | No valid session | Run `uip login` or `uip login` |
| `Project not found` | Invalid project ID | Check `UIPATH_PROJECT_ID` or create a new project via `push` |
| `dist/ not found` | App not built | Run `npm run build` first |
| `Version already exists` | Same version published | Bump version in `pack` step (e.g., `-v 2.0.0`) |
| `No packages found` | No `.nupkg` in `.uipath/` | Run `uip codedapp pack` first |
| `Folder key required` | Missing `UIPATH_FOLDER_KEY` | Set in `.env` or pass `--folderKey` |
| `App not found` on deploy | App not published | Run `uip codedapp publish` first |
| File conflicts on pull | Local files would be overwritten | Use `--overwrite` or manually resolve |

## References

- **[CLI Command Reference](references/commands-reference.md)** — Every `uip codedapp` command with parameters and examples
- **[File Sync Guide](references/file-sync.md)** — Push/pull workflows, auto-project creation, conflict handling
- **[Pack / Publish / Deploy Guide](references/pack-publish-deploy.md)** — Full deployment pipeline, options, metadata files
- **[Platform Operations](/uipath:uipath-platform)** — Authentication, Orchestrator, solutions (uipath-platform skill)
