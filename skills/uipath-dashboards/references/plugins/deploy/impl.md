# Deploy — mode impl

End-to-end workflow for Deploy mode. Ships a dashboard that Build produced. **Read this file only when Deploy is the chosen mode; never preload alongside `build/impl.md`.**

## Preamble

### Step 0 — Preflight
Same as Build. Halt if not logged into `uip`.

### Step 1 — Require state
Check `<cwd>/.uipath-dashboards/state.json`. Missing → halt: *"No dashboard built here. Run Build first."* Deploy never scaffolds.

### Step 2 — Resolve deploy-time folder AND clientId
Two values are needed at Deploy time that Build doesn't collect:

**(a) `folderKey`** — which Orchestrator folder hosts the deployed app (access control).
**(b) `clientId`** — a real non-confidential External App clientId. Required even though our runtime auth is secret-mode (postMessage/PAT), because `uip codedapp pack` validates `uipath.json`'s clientId server-side at deploy and **rejects the sentinel `00000000-...-0000`**. Earlier drafts of this skill assumed the sentinel would pass; it doesn't. Until the Apps API supports a no-clientId deploy path, we collect a real one at Deploy.

#### 2a — clientId
If `state.json.clientId` is null (typical post-Build):
1. Prompt the user:
   ```
   Deploying needs a non-confidential External App clientId (one-time per tenant).
   Our runtime auth doesn't use OAuth — this is just to satisfy `uip codedapp`'s
   server-side clientId validation. We'll reuse this value for future deploys.

   Open: https://<env>.uipath.com/<orgName>/<tenantName>/portal_/externalapps

     • Click "Add application" → Non-confidential → App type: "User"
     • Any scope will do (OR.Folders.Read is fine — runtime doesn't exercise it)
     • Copy the "App ID" and paste below.

   clientId: >
   ```
2. Validate format (GUID-shaped: 8-4-4-4-12 hex characters).
3. Write to `state.json.clientId` — persisted for all subsequent upgrades.
4. **Update `<project>/uipath.json`** — replace the sentinel clientId with this real value. Pack reads this file; old sentinel will block deploy.

If `state.json.clientId` is already set → skip; reuse the existing value; re-sync `uipath.json` to match in case the file was regenerated.

#### 2b — folderKey
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
- `state.json.folderKey` and `state.json.clientId` both populated (after Step 2a + 2b).
- `state.json.app.name`, `state.json.app.semver` populated.
- `<project>/uipath.json` has clientId matching `state.json.clientId` (NOT the sentinel `00000000-0000-0000-0000-000000000000`). If sentinel still present, Step 2a wasn't applied — re-run.
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
uip codedapp deploy -n <state.app.name> --folder-key <state.folderKey> --output json
```
**Both flags are required in non-interactive mode.** The CLI's behavior:
- Without `--folder-key`, `uip codedapp deploy` drops into an interactive folder picker. Agents running non-interactively hang and then fail with `User force closed the prompt`. Always pass the flag.
- **Do NOT pass `-v <semver>`.** The `-v` flag on deploy expects a server-side `deployVersion` integer (from publish output), NOT the semver. Passing `-v 1.0.0` right after a successful publish of 1.0.0 still errors with `App has not been published yet`. Omitting `-v` entirely lets the CLI deploy the latest published version — which is what we want 99% of the time. Only pass `-v` if you're intentionally pinning to a specific `Data.DeployVersion` integer from a prior `uip codedapp publish`.

Parse:
- Success → record `systemName`, `deploymentId`, `appUrl`, `deployedAt` from result.
- Stderr contains `clientId not found` → auto-hand off to [../../primitives/deploy-fallback.md](../../primitives/deploy-fallback.md) (direct-API).
- Stderr contains `User force closed the prompt` → `--folder-key` wasn't passed; regenerate the command with the flag and retry.
- Stderr contains `App has not been published yet` despite a successful publish → `-v` was passed with a semver; drop the `-v` flag and retry.
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
  "baseUrl": "https://<env>.uipath.com",
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
