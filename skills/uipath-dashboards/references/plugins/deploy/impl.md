# Deploy — mode impl

End-to-end workflow for Deploy mode. Ships a dashboard that Build produced. **Read this file only when Deploy is the chosen mode; never preload alongside `build/impl.md`.**

## Preamble

### Step 0 — Preflight
Same as Build. Halt if not logged into `uip`.

### Step 1 — Require state
Check `<cwd>/.uipath-dashboards/state.json`. Missing → halt: *"No dashboard built here. Run Build first."* Deploy never scaffolds.

### Step 2 — Resolve deploy-time folder
`state.json.folderKey` is typically `null` at this point — Build leaves it unset because folder is a Deploy concern (which Orchestrator folder hosts the app, not which folder's data the widgets query).

If `state.json.folderKey` is null:
1. Fetch folder list via SDK:
   ```ts
   import { Folders } from '@uipath/uipath-typescript';
   const folders = new Folders(sdk);
   const list = await folders.getAll();
   ```
2. Present numbered picker:
   ```
   Which Orchestrator folder should this app be deployed to?
   (This controls who can open the app via folder permissions — it's
    independent of which folder's data the widgets show.)
     1. Main       (a3f2-...)
     2. Shared     (b7c1-...)
     3. Engineering (d4e9-...)
     > 1
   ```
3. Write `state.json.folderKey` — persisted for subsequent upgrades.

If `state.json.folderKey` is already set (user deployed before, OR the Build prompt named a folder) → skip the picker; use the existing value.

### Step 3 — Classify deploy type
Read `state.json.deployment.systemName`:
- `null` → **Fresh deploy**
- non-null → **Upgrade deploy**

---

## Main flow

Pipeline: `Validate → Plan → Confirm → Build → Pack → Publish → Deploy → Update state → Report`

### Validate
- `<project>/package.json`, `vite.config.ts`, `uipath.json` exist.
- `<project>/src/dashboard/` non-empty (at least `Dashboard.tsx` + 1 widget).
- `state.json.folderKey` populated (after Step 2), `state.json.app.name`, `state.json.app.semver` populated.
- Halt with targeted error + fix hint on any miss.

### Plan
Show the user a deploy plan:
```
Deploy plan:
  Project     : ./<path>
  App name    : <name>  (routing: <routingName>)
  Version     : <semver>  (<bump suggestion or "unchanged">)
  Env         : <env>
  Org / Tenant: <org> / <tenant>
  Folder      : <folderName>  (key: <folderKey>)
  Deploy type : <fresh|upgrade>
```

If `app.semver` equals the last published semver, SUGGEST patch bump (`1.0.2` → `1.0.3`). Never silently bump.

### Confirm
**Critical Rule 5 — no auto-deploy.** Wait for explicit `y`/`n` from user. On `n` → clean exit. On overrides like "use 2.0.0" → accept, redraw plan, re-prompt.

### Build
`npm run build` in `<project>`. Halt if `dist/` missing or empty.

### Pack
```bash
uip codedapp pack dist -n <app.name> -v <app.semver> --output json
```
If pack emits `"⚠️ App name contains invalid characters. Using sanitized name: ..."`, rename the resulting lowercased nupkg to the original casing:
```bash
mv .uipath/<lower>.<ver>.nupkg .uipath/<OriginalCasing>.<ver>.nupkg
```

### Publish
```bash
uip codedapp publish -n <app.name> -v <app.semver> --output json
```
Parse `Data.DeployVersion` (server-side integer); record as `state.json.deployment.deployVersion`. Halt on "No package found matching name" with the casing-mismatch hint.

### Deploy
Try CLI happy path first:
```bash
uip codedapp deploy --output json
```
- Success → record `systemName`, `deploymentId`, `appUrl`, `deployedAt` from result.
- Stderr contains `clientId not found` → auto-hand off to [../../primitives/deploy-fallback.md](../../primitives/deploy-fallback.md) (direct-API).
- Any other error → surface, halt.

### Update state
Atomic write to `state.json.deployment`:
```json
{
  "systemName": "IDabc123...",
  "deploymentId": "dep-xyz",
  "deployVersion": 4,
  "appUrl": "https://<org>.<env-infix>uipath.host/<routingName>",
  "deployedAt": "<ISO>",
  "lastPublishAt": "<ISO>"
}
```
Per [../../primitives/state-file.md](../../primitives/state-file.md) (atomic `.tmp` + rename).

### Report
```
✓ Deployed: <appUrl>

Checklist:
• Load the URL above. Auth is iframe postMessage; host should pass your session token automatically.
• If the page loads but data is missing → check browser console for auth-strategy logs. The host isn't yet wired to respond to REFRESHTOKEN — see references/primitives/auth-strategy.md for the host-side spec you need to implement.
• For local preview: `cd <project> && npm run dev` — reuses your .env.local PAT.
```

---

## Fresh-vs-upgrade detection

Solely from `state.json.deployment.systemName`. Not from server state, not from folder listing.

| `systemName` | Type |
|---|---|
| `null` | **Fresh** — POST `/versions/<deployVersion>/deploy` |
| non-null | **Upgrade** — PATCH `/deployed/apps/<deploymentId>` |

If the server returns `1004 "app already deployed in folder"` on a fresh attempt, auto-reconcile via `assets/scripts/discover-deployment.sh` (list deployed apps in the folder, find by systemName, update state.json, retry as upgrade). One-time reconciliation.

## `uipath.json` in secret-mode

Contents (sentinel `clientId` satisfies CLI schema; runtime never reads it):
```json
{
  "clientId": "00000000-0000-0000-0000-000000000000",
  "scope": "",
  "orgName": "<from auth-context>",
  "tenantName": "<from auth-context>",
  "baseUrl": "https://<env>.api.uipath.com",
  "redirectUri": "https://<org>.<env-infix>uipath.host/<routingName>"
}
```

Known implementation unknown: does Apps service accept this sentinel? Test dry-run against alpha during development. If rejected, activate **Fallback 2** per [../../primitives/auth-strategy.md](../../primitives/auth-strategy.md) (tenant-wide External App, clientId referenced but no OAuth).

## Error paths

| Condition | Action |
|---|---|
| `state.json` missing | Halt: "No dashboard built here; run Build first." |
| `dist/` missing post-build | Halt with stderr. |
| Pack: invalid name | Halt; suggest cleaner name. |
| Publish: version exists | Halt; suggest semver bump; never silent-bump. |
| Deploy: `clientId not found` | Auto-fallback to direct-API. |
| Deploy: `1004 already deployed` on fresh attempt | Auto-reconcile via discover-deployment.sh; retry as upgrade. |
| Deploy: lowercase-routingName violation | Halt; user picks new routing; update state.json. |
| CLI 5xx | Retry 3× with exponential backoff (1s, 3s, 9s); then halt. |
| User aborts at `Proceed?` gate | Clean exit, no side effects. |

## What Deploy does NOT do

- Scaffold (Build-only).
- Regenerate code from prompt (ships what's on disk).
- `uip codedapp push/pull` Studio Web sync (→ `uipath-coded-apps`).
- Manage External Apps (auth-strategy handles if needed).
- Diagnose post-deploy runtime issues (points to auth-strategy.md and stops).
