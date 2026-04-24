# state-file

## Purpose
Schema + atomic read/write for `<project>/.uipath-dashboards/state.json`. Single source of truth for per-project config that both Build and Deploy share.

## Inputs
- Partial field updates (merged on write).

## Outputs
Atomic on-disk state file.

## Rules
1. **Location:** `<project>/.uipath-dashboards/state.json` — NEVER `<project>/.uipath/` (CLI territory).
2. **Gitignored by default.** Scaffold writes `.gitignore` entry on first Build.
3. **Atomic writes.** Write to `.uipath-dashboards/state.json.tmp`, rename to `state.json` on success.
4. **Read is tolerant of missing file** — returns schema defaults (see below).
5. **Schema versioned via `schemaVersion: 1`** for future migrations.

## Schema v1

```json
{
  "schemaVersion": 1,
  "env": "alpha",
  "orgName": "acme",
  "tenantName": "default",
  "folderKey": "a3f2-...",
  "app": {
    "name": "agent-health-dashboard",
    "routingName": "agent-health-dashboard",
    "semver": "1.0.0"
  },
  "deployment": {
    "systemName": null,
    "deploymentId": null,
    "deployVersion": null,
    "appUrl": null,
    "deployedAt": null,
    "lastPublishAt": null
  }
}
```

### Field ownership
| Field | Written by | Notes |
|---|---|---|
| `schemaVersion`, `env`, `orgName`, `tenantName` | `intent-capture` (first Build) | derived from `auth-context`; never prompted |
| `folderKey` | **Deploy** by default; Build only if the user's prompt explicitly scopes to a folder | Folder is a Deploy concern — which Orchestrator folder hosts the deployed app, not which folder's data the widgets query. See [../plugins/deploy/impl.md § Step 2](../plugins/deploy/impl.md). |
| `app.name`, `app.routingName`, `app.semver` | `intent-capture` (first Build), `deploy-cli` (semver bumps) | |
| `deployment.*` | `deploy-cli` or `deploy-fallback` (on successful deploy/upgrade) | |

### Atomic write recipe
```bash
DIR="<project>/.uipath-dashboards"
mkdir -p "$DIR"
# write new content to .tmp
cat > "$DIR/state.json.tmp" <<EOF
<json content>
EOF
# atomic swap
mv "$DIR/state.json.tmp" "$DIR/state.json"
```

On Windows (Git Bash / PowerShell), `mv` is atomic on the same filesystem. This is the discipline governance uses for audit records.

### Defaults for missing file
Returning schema defaults on read means callers can compose field-updates without pre-existence checks:
```
defaultState = {schemaVersion: 1, env: null, orgName: null, ..., deployment: {all nulls}}
```

### Migration (when v2 schema arrives)
Read `schemaVersion`. If < current, apply migration chain. If > current, halt with "This project was built with a newer skill version; update the skill."

### Error paths
| Condition | Action |
|---|---|
| State file exists but is malformed JSON | Halt: "Invalid state.json; investigate or delete + rebuild." Do NOT silent-overwrite (might lose data). |
| Disk full on write | Halt; .tmp file is left as evidence for debugging. |
| Concurrent write (two Build runs) | Atomic rename means last-writer-wins; no corruption. Document that concurrent Builds are not supported. |
