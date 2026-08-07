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

`pack` **copies `uipath.json` verbatim** into the package — it does **not** create, mint, or modify the client ID (verified on `codedapp-tool` 1.197). The `clientId` is set once at **scaffold time** (from the External Application) and carried through unchanged by every pack.

> **Do NOT pass `--reuse-client`.** The flag was removed from the CLI — passing it errors `unknown option '--reuse-client'`, and there is **no** client option on `pack` at all. `uipath.json` is the single source of truth: ensure `clientId` is correct there **before** packing. Older docs that say "first pack creates a client" or "pass `--reuse-client` to reuse it" are stale.

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

> **Action apps — always pass `--type Action`.** `publish` defaults to `--type Web`. An action app published without `--type Action` registers as a Web app and will **not** bind to Action Center tasks. Pass `--type Action` on **every** publish of an action app — first deploy and every version update. Never omit it, never rely on the default.

### What Happens Internally

1. Selects the `.nupkg` file (auto-select, by name, or interactive)
2. Uploads the package to Orchestrator via the OData API — needs Orchestrator scopes (`OR.Folders`, `OR.Execution`, `OR.Administration`, or `OR.Default`)
3. Registers the coded app with the UiPath Apps service — needs `Apps.Read Apps.Write`
4. Creates `.uipath/app.config.json` with registration metadata

> **Steps 2 and 3 hit different services with different scope requirements.** The `uip login` session `--scope` must cover **both**. If it has only Orchestrator scopes, step 2 succeeds and step 3 silently 401s ("Registering coded app" fails). Interactive `uip login` grants a broad default that includes both; client-credentials logins must list `Apps.Read Apps.Write` explicitly. These are the *CLI session* scopes — separate from the runtime OAuth scopes in `uipath.json`.

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

> **`appUrl` may stay `null` here even after a successful deploy** (known gap, [APPS-35784](https://uipath.atlassian.net/browse/APPS-35784)). Read the deployed URL from the `deploy` command's stdout, not from this file.

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
| `-v, --version <version>` | Target a **specific published version** (different semantic from `pack`/`publish`'s `-v`). **Prefer omitting it** — let it default to Latest. Passing a version that the catalog hasn't finished indexing yields a misleading `"...has not been published yet"` error. | Latest |
| `--folder-key <key>` | UiPath folder **key** (GUID, not the name). **Always pass explicitly** — see below. | From `UIPATH_FOLDER_KEY` env var, else interactive (avoid) |
| `--path-name <slug>` | URL slug for the app. **First deploy ONLY** — omit on upgrades, else `routing name must be unique` (see [Upgrading an existing app](#upgrading-an-existing-app)). Cannot contain reserved words. | App name |
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

### Upgrading an existing app

An upgrade is just Pack → Publish → Deploy with a **bumped version** — `deploy` auto-detects the existing app and upgrades it in place. Rules that keep an upgrade reliable and on the **same URL the user already shared**:

1. **Bump the version** on `pack`/`publish` (re-using a version fails `Version already exists`).
2. **Omit `--path-name`.** The URL slug already exists; re-passing it errors `routing name must be unique`. Omitting it upgrades the app **at its current URL** — no new URL is minted. Pass `--path-name` only on the *first* deploy of a brand-new app.
3. **Omit `-v` / `--version`** on `deploy` — let it default to Latest. Targeting a just-published version the catalog hasn't finished indexing yields a misleading `...has not been published yet`.
4. **Don't change `clientId`** in `uipath.json` between versions — `pack` carries it through verbatim, so it stays unless you edit the file; a changed client ID breaks the deployed app's auth.
5. **Looks stale after upgrade? It's browser cache.** `deploy` prints the canonical `…/<app-name>` URL, but the user's existing vanity path keeps serving — the new build is live. Hard-refresh (Cmd/Ctrl+Shift+R) to confirm.

> **Keep the CLI current.** In-place upgrade auto-detect works on current `codedapp-tool` (verified on 1.197). If upgrades behave inconsistently across machines, they're likely on different tool versions — run `uip tools update` to align them, and compare `uip tools list --output json`.

#### Upgrade identity — historically fragile, now robust

On **older** `codedapp-tool` builds, `deploy` matched an existing deployment by the app's **portal display name**, so renaming the app in the portal — or `pack` silently sanitizing a spaced name — made the CLI lose the deployment and fall into a fresh deploy that then collided:

```
This app name is already deployed in this folder. Please choose a different name.
HTTP 400 · code 1004 · "app already deployed in folder"
```

That was [APPS-35627](https://uipath.atlassian.net/browse/APPS-35627). **Verified fixed on `codedapp-tool` 1.197 for CLI-deployed apps:** `deploy` resolves the app by name/systemName **server-side** and upgrades in place even when the portal display name differs — and even with no local `.uipath/app.config.json`. So the old "never rename / display name must equal `-n`" rule is **not required** on current builds.

Still worth doing as cheap insurance:

- **Pick a clean lowercase-kebab `-n` up front and keep it stable.** `pack` silently **lowercases and deletes spaces/invalid characters** (`"My Jobs App"` → `myjobsapp` — spaces removed, not hyphenated), so a spaced or mixed-case name becomes something you didn't intend.
- **Portal-first apps (unverified):** an app first created in the **portal** (never CLI-deployed) hasn't been tested on this upgrade path. If the CLI can't find it, align the portal display name to `-n` and confirm the folder key + account access before upgrading.

If you ever do get stuck on `1004` and can't re-align, delete the deployment from the **Orchestrator UI** and redeploy fresh — there is no `undeploy` / `--force` flag yet ([APPS-35784](https://uipath.atlassian.net/browse/APPS-35784)).

#### URL reserved words

The **app name** (`-n`) may contain words like `uipath` or `microsoft`, but the **URL slug** (`--path-name`) cannot — the platform rejects reserved words with HTTP 400 `reserved`. If the derived slug is rejected, use a variant (e.g. `microsof-…`). Only relevant on the first deploy (when `--path-name` is set).

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

`uip or folders list` returns folders the **current user** has access to (personal workspaces, solution folders, and standard folders), **paginated at 50 per page**. If the target folder might be beyond the first page — or a name you expect returns no match — pass `--all` to enumerate every accessible folder before matching.

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
# Non-interactive flow with explicit options — every flag passed, no prompts.
# --scope MUST include Apps.Read Apps.Write, or publish's "Registering coded app"
# step 401s even though the package upload succeeds (see publish internals above).
uip login --client-id $CLIENT_ID --client-secret $CLIENT_SECRET \
  --scope "OR.Folders OR.Execution OR.Administration Apps.Read Apps.Write"
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
| Pack shows wrong clientId | Stale `uipath.json` | `pack` copies `uipath.json` verbatim — it doesn't manage the client ID. Fix `clientId` in `uipath.json`. Do NOT pass `--reuse-client` (removed from the CLI). |
| `unknown option '--reuse-client'` | Passing a removed flag | Drop `--reuse-client` — reuse is the default now. |
| `routing name must be unique` on upgrade | `--path-name` re-passed on an upgrade | Omit `--path-name`; it's first-deploy only (see [Upgrading an existing app](#upgrading-an-existing-app)). |
| App gets a **new URL** on upgrade | `--path-name` passed on upgrade minted a fresh slug | Omit `--path-name` on upgrades to keep the existing URL the user already shared. |
| Deployed app looks stale after upgrade | Browser cache on the vanity path | Hard-refresh (Cmd/Ctrl+Shift+R); the new build is already live. |
| `This app name is already deployed in this folder` / HTTP 400 `code 1004` | **Older CLI** matched by display name and lost the existing app (APPS-35627 — fixed on 1.197+) | Update the CLI (`uip tools update`). If it persists (e.g. a portal-first app), align the portal display name to `-n` and redeploy; if unrecoverable, delete via the Orchestrator UI. See [Upgrade identity](#upgrade-identity--historically-fragile-now-robust). |
| `pack` sanitized the app name (e.g. `My Jobs App` → `myjobsapp`) | Name has spaces/capitals/invalid chars | `pack` lowercases and deletes spaces. Use a clean lowercase-kebab `-n` up front. |
| `Published app with package name '<name>' already exists` (on publish) | App name already registered **in the tenant** (names are tenant-unique at registration) | Choose a different, distinctive `-n` (generic names like `my-app` are often taken). |
| Upgrade shipped the **wrong (older) version** | Old CLI defaulting `deploy` to the oldest version | Update the CLI (`uip tools update`); if it persists, pin the target explicitly with `-v <version>`. |
