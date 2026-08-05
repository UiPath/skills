# Pack / Publish / Deploy Guide

Guide for packaging, publishing, and deploying UiPath Coded Web Applications through either an explicit testing-only lane or a governed release lane.

## Choose the lane before publishing

| Lane | Eligible use | Required boundary |
|------|--------------|-------------------|
| **Testing-only quick path** | User explicitly requests an internal, synthetic-data deployment to UiPath Alpha or Staging | Bind the exact target, profile, client, route, candidate bytes, and `create`/`upgrade` intent in an automatic testing receipt. Dirty source is allowed but is not provenance. No second approval is required. |
| **Governed release** | Production, customer data, or any request for durable release evidence | Use reviewed source, exact dist/package/runtime hashes, remote target evidence, explicit approval, immutable receipt, rollback authority, and post-deploy verification. |

Ambiguity defaults to governed. The testing lane must state `production_eligible: false` and `release_evidence: false`; it cannot be promoted into a governed receipt after execution.

Before either lane writes remotely, choose one intent:

- **Create** — fresh remote inventory proves there is no matching deployment and the exact route is unused.
- **Upgrade** — fresh remote inventory proves the exact existing deployment, system name, route, current version, and candidate version.

`.uipath/app.config.json`, dashboard state, and prior command output are local hints only. If remote evidence cannot establish exactly one intent, stop. Never use automatic upsert behavior as the decision maker.

The stock `uip codedapp` 1.198.0 surface has no deployment `list` or `get`. It may execute a preflighted `publish`/`deploy`, but it cannot establish authoritative create/upgrade state by itself. Use an approved inventory-capable deployment helper or Apps API runtime without exposing bearer tokens. If none is available, stop before the write.

### Automatic testing receipt

Before the first external write, create a new receipt at `.uipath/testing-evidence/<UTC>-<app>-<version>.json` (or an equivalently ignored release-evidence directory) and atomically claim the exact candidate/target in `<receipt>.claim` using create-if-absent semantics. Verify the directory is ignored with `git check-ignore`; if it is tracked or not ignored, choose an ignored evidence directory before continuing. Use policy version `codedapp-testing-only/1.0`. Minimum fields:

- `kind: "uipcodedappdeploy.testing-receipt"`, `schemaVersion: "1.0"`
- `authorization.mode: "explicit_testing_request"`
- Exact environment/control plane, org, tenant, folder, profile, CLI version/path, app/package, client, route, intent, candidate version, and artifact/config hashes
- Git HEAD and worktree-status digest as context only
- `data_classification: "synthetic_only"`, `production_eligible: false`, `release_evidence: false`
- Fixed waived gates and non-waivable policy version
- Per-stage timestamps/results and one terminal status: `failed_prewrite`, `publish_indeterminate`, `published_not_deployed`, `deploy_indeterminate`, `deployed_unverified`, or `succeeded_testing`

For `codedapp-testing-only/1.0`, record these exact sorted arrays; do not invent or omit values:

```json
{
  "waived_gates": [
    "absent_backend_and_realtime_certification",
    "clean_source_provenance",
    "full_multi_role_and_pilot_certification",
    "independent_release_approval",
    "protected_release_environment",
    "rebuild_and_full_suite_for_exact_audited_candidate",
    "second_plan_hash_approval",
    "signed_production_receipt"
  ],
  "nonwaivable_gates": [
    "alpha_or_staging_target",
    "automatic_receipt_and_atomic_claim",
    "bundle_audit_and_postdeploy_verification",
    "exact_target_profile_client_route_and_artifact_binding",
    "explicit_create_or_upgrade",
    "internal_authenticated_access",
    "no_route_mutation_delete_recreate_or_blind_retry",
    "no_secret_exposure",
    "synthetic_data_only"
  ]
}
```

Do not include `plan_hash`, `approved_plan_hash`, tokens, secrets, environment dumps, or unredacted response bodies. Release the candidate claim only after a handled pre-write failure. Retain it after any possible external write. There is no resume: reconciliation plus a fresh explicit testing request creates a new receipt.

Use SHA-256. Hash package files as exact bytes; hash runtime JSON after UTF-8 canonical serialization with sorted keys; hash `dist/` as the sorted list of relative paths plus each file's SHA-256 and size so timestamps and archive metadata cannot change the identity. Write receipt updates to a sibling temporary file, flush, then atomically rename.

This skill documents but does not fabricate a governed executor. If the environment does not provide a reviewed approval/receipt/rollback implementation for governed release, stop and report that release gate rather than writing an ad hoc JSON file.

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

The exception is an exact already-published candidate selected after remote reconciliation: deploy that candidate directly rather than rebuilding or republishing it.

## Pack

Package the app build output into a `.nupkg` file with UiPath metadata.

### Basic Usage

```bash
# Pack with interactive prompts
uip codedapp pack dist

# Pack with all options specified
uip codedapp pack dist -n my-webapp --version 1.0.0 --author "My Team" --description "Production app"
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `<dist>` | Path to build output directory | **Required** |
| `-n, --name <name>` | Package name | Prompted |
| `-v, --version <version>` | Package version | `1.0.0` |
| `-o, --output <dir>` | Output directory for `.nupkg` | `./.uipath` |
| `--author <author>` | Package author | `UiPath Developer` |
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

`pack` does not create, select, or reuse an OAuth client. Configure the non-confidential client in `uipath.json`, verify it against the target tenant, and pass the exact client explicitly to `deploy` with `--client-id <GUID>` when required. If the client or its scopes/redirects change after a governed plan is approved, invalidate that plan and re-bind the configuration. For testing, re-hash the configuration and start a new testing receipt.

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

This file is consumed by `deploy` to resolve the app name automatically. Preserve it between publish and deploy, but do not treat it as remote authority. Compare its system/deployment identifiers with fresh remote inventory before choosing `create` or `upgrade`.

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

Deploy or upgrade a coded app in UiPath. The CLI can auto-detect, but an agent must not delegate the create/upgrade decision to that behavior: prove the intended operation from remote state first.

### Basic Usage

```bash
# Proven create: bind route, client, version, folder, and profile
uip codedapp deploy -n my-webapp --version 1.0.0 \
  --path-name my-webapp --client-id <client-guid> \
  --folder-key <folder-guid> --profile <profile> --output json

# Proven upgrade: preserve the existing route by omitting --path-name
uip codedapp deploy -n my-webapp --version 1.1.0 \
  --client-id <client-guid> --folder-key <folder-guid> \
  --profile <profile> --output json
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-n, --name <name>` | App name | From `app.config.json` or prompted |
| `-v, --version <version>` | Exact published candidate to deploy. Verify it is indexed before deployment; never omit this merely to select an unreviewed Latest version. | Latest |
| `--folder-key <key>` | UiPath folder **key** (GUID, not the name). **Always pass explicitly** — see below. | From `UIPATH_FOLDER_KEY` env var, else interactive (avoid) |
| `--org-name <name>` | Organization name (for app URL) | From `.env` |
| `--path-name <name>` | Permanent hosted route; pass only for a proven create | Generated/defaulted by tool |
| `--client-id <id>` | Exact non-confidential OAuth client | Tool/config default |
| `--tags <tags>` | Comma-separated categorization tags | None |
| `--profile <name>` | Named authenticated CLI profile | Active/default profile |

### Create vs. Upgrade

| Intent | Preconditions | Route handling |
|--------|---------------|----------------|
| **Create** | Exact deployment absent and route unused in fresh remote inventory | Pass the reviewed `--path-name`; a collision stops the operation |
| **Upgrade** | Exact deployment/system/route/current version match fresh remote inventory | Omit `--path-name`; preserve and verify the existing route |

The command resolves the app name from:
1. `--name` flag (highest priority)
2. `.uipath/app.config.json` (created by `publish`)
3. Interactive prompt (fallback)

Resolution convenience is not authorization. Always pass the name and all available target flags explicitly. For upgrades, verify that the local config identifies the same remote deployment before executing.

### External-write failure boundary

Once `publish` or `deploy` starts, a timeout, interruption, 5xx, HTML response, or nonzero exit may still have changed remote state. Do not immediately retry. Re-read remote package/deployment state and create a fresh operation from the reconciled result.

Never respond to a conflict by:

- Auto-bumping and republishing an unreviewed version.
- Generating a random route or omitting the intended route.
- Deleting and recreating the deployment.
- Falling back from upgrade to create.
- Assuming `.uipath/app.config.json` proves what happened remotely.

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

# 3. Bind the key into the separately preflighted create or upgrade operation
test -n "$FOLDER_KEY" && printf '%s\n' "$FOLDER_KEY"
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

## Pipeline Examples

### Testing-only Alpha/Staging create

The user must explicitly request a synthetic/internal test. Record an automatic testing receipt and confirm the route is unused before these writes.

```bash
# 1. Authenticate with an exact non-production profile
uip login status --profile "$PROFILE" --output json

# 2. Build the app
npm run build

# 3. Pack an explicit version
uip codedapp pack dist -n my-webapp --version 1.0.0 -o .uipath

# 4. Publish the exact candidate
uip codedapp publish -n my-webapp --version 1.0.0 --profile "$PROFILE" --output json

# 5. Create on the preflighted route
uip codedapp deploy -n my-webapp --version 1.0.0 \
  --path-name my-webapp --client-id "$CLIENT_ID" \
  --folder-key "$FOLDER_KEY" --profile "$PROFILE" --output json
```

### Testing-only Alpha/Staging upgrade

Re-read and match the exact existing deployment before executing. The route is immutable and therefore omitted.

```bash
# 1. Build and pack the chosen candidate version
npm run build
uip codedapp pack dist -n my-webapp --version 2.0.0 -o .uipath

# 2. Publish the exact candidate
uip codedapp publish -n my-webapp --version 2.0.0 --profile "$PROFILE" --output json

# 3. Upgrade the reconciled deployment; never pass or change its route
uip codedapp deploy -n my-webapp --version 2.0.0 \
  --client-id "$CLIENT_ID" --folder-key "$FOLDER_KEY" \
  --profile "$PROFILE" --output json
```

### Governed CI/CD release

The reviewed plan supplies the exact values and hashes below. The named profile must be provisioned securely before the job; never put a client secret or bearer token in command arguments.

```bash
npm run build
uip codedapp pack dist -n "$APP_NAME" --version "$VERSION" -o .uipath
uip codedapp publish -n "$APP_NAME" --version "$VERSION" --profile "$PROFILE" --output json
uip codedapp deploy -n "$APP_NAME" --version "$VERSION" \
  --client-id "$CLIENT_ID" --folder-key "$FOLDER_KEY" \
  --profile "$PROFILE" --output json
```

### Agent flow (user provides folder name only)

```bash
# 1. Resolve folder name → key
FOLDER_KEY=$(uip or folders list --output json \
  | python3 -c "import json,sys;d=json.load(sys.stdin);m=next((x for x in d['Data'] if x['Name']=='$USER_FOLDER_NAME'),None);print(m['Key'] if m else '')")

[ -z "$FOLDER_KEY" ] && { echo "Folder '$USER_FOLDER_NAME' not found"; exit 1; }

# 2. Use the key in the separately preflighted create or upgrade command
uip codedapp deploy -n "$APP_NAME" --version "$VERSION" \
  --client-id "$CLIENT_ID" --folder-key "$FOLDER_KEY" \
  --profile "$PROFILE" --output json
```

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `No packages found` | Missing `.nupkg` | Run `uip codedapp pack` first |
| `Version already exists` | Candidate version conflicts with remote state | Reconcile whether the attempted publish succeeded. If it did not, select and review a new version before packing; never auto-bump and retry. |
| `App not found` on deploy | App not published | Run `uip codedapp publish` first |
| `Folder key required` / deploy hangs on prompt | Missing folder key | Resolve via `uip or folders list --output json`, then run `uip codedapp deploy --folder-key <key> ...` (or `UIPATH_FOLDER_KEY=<key>` env-var prefix). |
| `Missing tenant name` on publish | `UIPATH_TENANT_NAME` not set | Set in `.env` or pass `--tenant-name` |
| `dist/ not found` | App not built | Run `npm run build` |
| OAuth client is wrong | `uipath.json`, deploy flags, or remote client differ | Stop; verify the exact client and target. Re-bind governed evidence or begin a new testing receipt before changing configuration. |
| `routing name must be unique` | Route is occupied or upgrade was misclassified | Stop and reconcile remote state. Never randomize or omit a reviewed route and retry. |
| Publish/deploy timeout, 5xx, HTML, or interruption | External write may have succeeded | Treat as indeterminate; inspect remote state before forming a fresh operation. |
