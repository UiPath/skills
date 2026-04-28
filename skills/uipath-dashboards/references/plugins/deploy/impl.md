# Deploy — mode impl

End-to-end workflow for Deploy mode. Ships a dashboard that Build produced. **Read this file only when Deploy is the chosen mode; never preload alongside `build/impl.md`.**

## Preamble

### Step 0 — Preflight
Same as Build. Halt if not logged into `uip`.

### Step 1 — Require state
Resolve project: `<cwd>/.uipath-dashboards/<name>/` (where `<name>` is from prompt or — if only one project in workspace — auto-picked, with the choice confirmed in the deploy plan). Check `<project>/.dashboard/state.json`. Missing → halt: *"No dashboard built here. Run Build first."* Deploy never scaffolds. If workspace has multiple projects and the user didn't specify a name, ask which to deploy.

### Step 2 — Resolve `folderKey`

Which Orchestrator folder hosts the deployed app. If `state.json.folderKey` is already set (user deployed before, OR the Build prompt named a folder) → skip Step 2 entirely; use the existing value.

If `state.json.folderKey` is `null`:

#### When the user named a folder (preferred — single round-trip)
If the prompt mentioned a folder name (e.g., "deploy this to Shared", "publish to NishankFolder"), look it up by name in one call. **Always pass `--all`** — without it, the CLI returns only folders the calling user already has explicit access to, which often misses the folder the user is actually naming.

```bash
uip or folders list --all -n "<folder-name>" --output json
```

Parse `Data[0].Key` and `Data[0].DisplayName`. Empty result → halt with: *"No folder named '<x>' found in this tenant (searched all access scopes). Pick from the full list, or cancel."*

#### When the user didn't name a folder (interactive picker)
```bash
uip or folders list --all --output json
```

Parse `Data[]`. **Watch for truncation** — the default page cap is 50. If `Data.length === 50`, surface a warning to the user and re-run with a higher cap or a name filter:
```
Warning: tenant has 50+ folders; showing first 50. If you don't see yours,
re-run "deploy this dashboard to <name>" naming the folder explicitly.
```

Present a numbered picker:
```
Which Orchestrator folder should this app be deployed to?
(This controls who can open the app via folder permissions — it's
 independent of which folder's data the widgets show.)
  1. Main       (a3f2-...)
  2. Shared     (b7c1-...)
  3. Engineering (d4e9-...)
  > 1
```

Write `state.json.folderKey` — persisted for subsequent upgrades.

#### CLI shorthand reminder
The Orchestrator namespace is `uip or` — **NOT** `uip orchestrator` (which the CLI does not recognize). All folder/job/asset commands use the abbreviation.

### Step 3 — Classify deploy type
Read `state.json.deployment.systemName`:
- `null` → **Fresh deploy**
- non-null → **Upgrade deploy**

---

## Main flow

Pipeline: `Validate → Plan → Confirm → Build → Pack → Publish → Deploy → Update state → Report`

### Validate
- `<project>/package.json`, `vite.config.ts`, `uipath.json` exist.
- `<project>/public/action-schema.json` exists (Vite copies it into `dist/` at build).
- `<project>/src/dashboard/` non-empty (at least `Dashboard.tsx` + 1 widget).
- `state.json.folderKey` populated (after Step 2).
- `state.json.app.name` (display), `state.json.app.routingName` (slug), `state.json.app.semver` populated.
- Halt with targeted error + fix hint on any miss.

### Plan
Show the user a deploy plan:
```
Deploy plan:
  Project       : ./<path>
  Routing name  : <state.app.routingName>    ← deploy slug AND catalog title (current CLI behavior)
  Version       : <semver>  (<bump suggestion or "unchanged">)
  Env           : <env>
  Org / Tenant  : <org> / <tenant>
  Folder        : <folderName>  (key: <folderKey>)
  Deploy type   : <fresh|upgrade>
  Pin on deploy : <pinned|not pinned|ASK>     ← required user input — see Pin-on-deploy detection below
```

**Note on the displayed title.** Dashboards deploy as Coded Action Apps and surface in the **Governance Unified Portal** (NOT in the generic Apps catalog). The deployed app's catalog title comes from `deploy -n "<state.app.name>"` (the friendly Title Case name); the URL slug comes from `--routing-name "<state.app.routingName>"`. These are two different values — `-n` is what users see, `--routing-name` is the path identifier.

If `app.semver` equals the last published semver, SUGGEST patch bump (`1.0.2` → `1.0.3`). Never silently bump.

**Pin-on-deploy detection.** **There is no default — the user must choose explicitly.**

Pinning surfaces the dashboard on the **Governance Unified Portal home**; not pinning leaves it folder-visible only. The choice has user-facing consequences and we don't pre-select for them. Note: dashboards do NOT appear in the generic UiPath Apps homepage at any point — Governance Unified Portal home is the only place pinning affects.

Detection logic:

1. Scan the user's prompt (current message AND the original Build prompt that produced this dashboard) for explicit pin signals:
   - **Pin = yes** when prompt contains: `pin`, `pin to home`, `pin on portal`, `surface on home`, `show on portal home`, `pin to governance`.
   - **Pin = no** when prompt contains: `don't pin`, `do not pin`, `without pinning`, `no pin`, `deploy only`, `skip pin`, `don't surface`.
2. If a signal is present, set `Pin on deploy: pinned` or `not pinned` in the plan and proceed.
3. If NO signal is present, the plan's `Pin on deploy` line reads `ASK`. The Confirm step then surfaces an explicit pin question (see below) BEFORE accepting the deploy.

This adds at most one extra round-trip when the user said `deploy this dashboard` with nothing else; in exchange we never silently surface a dashboard in places the user didn't intend.

### Confirm
**Critical Rule 5 — no auto-deploy.** Wait for explicit `y`/`n` from user. On `n` → clean exit. On overrides like "use 2.0.0" → accept, redraw plan, re-prompt.

**If `Pin on deploy: ASK`** (prompt was silent on pinning), include this question in the same message as the y/n confirm:

```
One more question before I deploy:

Should this dashboard be **pinned** on the Governance Unified Portal home?
  • **Pinned** — appears on the Governance Unified Portal home, visible at first glance.
  • **Not pinned** — accessible via the assigned folder, but doesn't surface on home.

(Dashboards never appear in the generic Apps homepage — pinning only affects the Governance Unified Portal home.)

Reply with `pin` or `don't pin` along with your y/n confirmation.
Examples: `y, pin it`  /  `y, no pin`  /  `n` (cancel deploy).
```

Accept any of:
- `y, pin it` / `yes pin` / `y pinned` → confirmed AND pin = yes.
- `y, no pin` / `yes don't pin` / `y, deploy only` → confirmed AND pin = no.
- Plain `y` with no pin opinion → re-prompt the pin question alone (don't proceed).
- `n` → clean exit.

Once both choices are captured, proceed to Build/Pack/Publish/Deploy with the resolved `--description "PINNED"` flag (pin = yes) or omitted (pin = no).

### Build
Production builds **must not include** `VITE_UIPATH_PAT` — anyone with the deployed bundle could extract it. Auth in production runs through the SDK's `ActionCenterTokenManager` (no client-side PAT needed). The `failBuildIfPatSet` plugin in `vite.config.ts` aborts `npm run build` if it detects the PAT in any loaded env file (`.env`, `.env.local`, `.env.production`, `.env.production.local`).

To produce a clean build, **temp-move `.env.local` aside** before invoking `npm run build`, restore on completion. This is a single-step recipe; do NOT skip the restore (the user still needs `.env.local` for local-dev preview):

```bash
# Move dev .env.local out of the way so the production build sees no PAT
[[ -f <project>/.env.local ]] && mv <project>/.env.local <project>/.env.local.deploy-backup

# Build
( cd <project> && npm run build )
BUILD_EXIT=$?

# Restore unconditionally (success OR failure)
[[ -f <project>/.env.local.deploy-backup ]] && mv <project>/.env.local.deploy-backup <project>/.env.local

# Honor the build's exit code
[[ $BUILD_EXIT -ne 0 ]] && exit $BUILD_EXIT
```

Halt if `dist/` missing or empty. Vite copies `public/action-schema.json` into `dist/` automatically. **Verify `<project>/action-schema.json` exists at the project root too** — `uip codedapp publish` reads the schema from CWD (the project root), not from `dist/`. If the project predates this rule, copy `public/action-schema.json` → `<project>/action-schema.json` before publish.

### Pack
```bash
uip codedapp pack dist -n <state.app.routingName> -v <state.app.semver> --output json
```
**`-n` on `pack` is the package name** — the nupkg filename identifier. Pass the routing name (lowercase slug) so the nupkg matches what `publish` expects. The user-friendly display name is supplied separately to `deploy` via its own `-n` flag, which on `deploy` carries different semantics (App name).

If pack emits `"⚠️ Package name contains invalid characters. Using sanitized name: ..."`, the routingName generator produced something the server doesn't like — halt and surface the message; the agent fix is to regenerate with `intent-capture`'s recipe.

### Publish
```bash
uip codedapp publish --type Action -n <state.app.routingName> -v <state.app.semver> --output json
```

**`-n` on `publish` is the package name** (matches pack). **`--type Action` is required** — it tells the platform to publish the nupkg as a coded action app, which consumes the action-schema bundled in `dist/`.

Wrap this call in the [transient-error retry loop](#transient-error-retry-loop). Parse `Data.DeployVersion` (server-side integer); record as `state.json.deployment.deployVersion`. Halt on "No package found matching name" with the casing-mismatch hint.

### Deploy
Pin = yes:
```bash
uip codedapp deploy \
  -n "<state.app.name>" \
  --routing-name "<state.app.routingName>" \
  --folder-key "<state.folderKey>" \
  --description "PINNED" \
  --output json
```

Pin = no:
```bash
uip codedapp deploy \
  -n "<state.app.name>" \
  --routing-name "<state.app.routingName>" \
  --folder-key "<state.folderKey>" \
  --output json
```

**Flag discipline:**
- `-n` on `deploy` is the **App name** — pass the user-friendly display title (`Agent Health Dashboard`). The deployed app's catalog title comes from this. Pack/publish use `-n` differently (package identifier = routing slug); deploy is the only command where `-n` carries the friendly name.
- `--routing-name` is the **URL slug** (`govdash-agent-health-x7k2`) and identifies which published package to deploy. Required even though it equals what we passed to publish; deploy doesn't infer it.
- `--description "PINNED"` is the **pin signal**. The Governance Unified Portal frontend reads the deployment description and pins the dashboard on its home when the value equals `PINNED`. Pass it when the user said yes; omit it entirely (don't pass `--description ""`) when the user said no.
- `--folder-key` is required in non-interactive mode. Without it, the CLI drops into an interactive folder picker; agents hang with `User force closed the prompt`.
- **Do NOT pass `-v <semver>`.** The `-v` flag on deploy expects a server-side `deployVersion` integer (from publish output), NOT the semver. Passing `-v 1.0.0` right after a successful publish of 1.0.0 still errors with `App has not been published yet`. Omitting `-v` lets the CLI deploy the latest published version.

Wrap this call in the [transient-error retry loop](#transient-error-retry-loop).

Parse:
- Success → record `systemName`, `appUrl` from result. Set `deployedAt = <ISO now>`. `deploymentId` may be absent — leave null per [state-file.md](../../primitives/state-file.md).
- Stderr contains `routingName already exists` / `Routing name is already taken` → **routing-name collision**. See [Routing-name retry](#routing-name-retry) below.
- Stderr contains `User force closed the prompt` → `--folder-key` wasn't passed; regenerate the command with the flag and retry.
- Stderr contains `App has not been published yet` despite a successful publish → `-v` was passed with a semver; drop the `-v` flag and retry.
- Stderr contains `1004` / `app already deployed in folder` → auto-reconcile via `assets/scripts/discover-deployment.sh`, populate `state.deployment.systemName/deploymentId`, retry as upgrade (PATCH).
- Any other error → surface, halt.

### Update state
Atomic write to `state.json.deployment` per [../../primitives/state-file.md](../../primitives/state-file.md). `deploymentId` may be `null` after a fresh deploy — that's expected; it gets backfilled at first upgrade reconciliation. **Bump `state.app.semver`** to the next patch version on success so the next deploy plan starts from a fresh number.

### Report

The CLI does **not** print a deployed app URL. Construct it deterministically from state:

```
APP_URL="https://${state.orgName}.${state.envInfix}uipath.host/${state.app.routingName}"
# envInfix: "alpha." for alpha, "" for prod (cloud → {org}.uipath.host)
# Example: https://appsdev.alpha.uipath.host/gov-dashboard-agent-health-e86b
```

Other URL shapes that look reasonable but DON'T resolve for deployed coded apps (do not surface them):
- `https://<env>.uipath.com/<org>/<tenant>/apps_/default/<routingName>` — 404
- `https://<env>.uipath.com/<org>/<tenant>/apps_/run/<systemName>` — 404

URL-first report — show the URL and the deployed-app fingerprint, nothing else:

```
✓ Deployed
  URL          : <appUrl>
  App name     : <state.app.routingName>          ← what the catalog shows today
  Version      : <state.app.semver>  (deploy version <state.deployment.deployVersion>)
  System name  : <state.deployment.systemName>
  Folder       : <folderName>  (<state.folderKey>)
  Pinned       : <yes|no>
  Deployed at  : <state.deployment.deployedAt>
```

No checklist, no auth-strategy hints, no "for local preview" reminders — those are noise after a successful deploy. Diagnostics are on-demand via the user asking, not pre-emptive.

---

## Transient-error retry loop

`uip codedapp publish` and `uip codedapp deploy` go through the UiPath edge (Cloudflare → origin). The origin can return transient 5xx (commonly 520/522/524 — origin unreachable). The CLI does NOT retry on its own; agents must.

**Prescriptive recipe — wrap every `uip codedapp publish` and `uip codedapp deploy` call in this:**

```bash
attempt() {
  local cmd="$1"
  local sleeps=(5 10 20)
  local resp
  for i in 0 1 2 3; do
    resp=$(eval "$cmd" 2>&1) || true
    # Cloudflare origin errors arrive as HTML even with --output json, with
    # "Bad gateway" / "Web server is down" / status codes 520/522/524.
    if echo "$resp" | grep -qE '<!DOCTYPE html>|cloudflare|HTTP 5[0-9][0-9]|Bad gateway|Web server is (down|unreachable)'; then
      if [[ $i -lt 3 ]]; then
        echo "Upstream gateway error — retrying in ${sleeps[$i]}s (attempt $((i+2))/4)..." >&2
        sleep "${sleeps[$i]}"
        continue
      fi
      echo "Upstream gateway error — exhausted retries. Try again in a few minutes." >&2
      return 1
    fi
    # Real error or success — return as-is.
    echo "$resp"
    return 0
  done
}

# Usage:
RESP=$(attempt 'uip codedapp publish --type Action -n "$ROUTING_NAME" -v "$SEMVER" --output json')
# Build deploy command — append --description "PINNED" by default; omit when pin=no.
DEPLOY_CMD='uip codedapp deploy -n "$APP_NAME" --routing-name "$ROUTING_NAME" --folder-key "$FOLDER_KEY"'
[[ "$PIN" == "yes" ]] && DEPLOY_CMD+=' --description "PINNED"'
DEPLOY_CMD+=' --output json'
RESP=$(attempt "$DEPLOY_CMD")
```

Sleeps `5s, 10s, 20s` between attempts (4 attempts total). **Always collapse Cloudflare HTML to a one-line message** — the raw HTML is up to 4KB of useless markup that drowns the real signal.

---

## Routing-name retry

If deploy fails with a routing-name uniqueness error (the slug is already taken in this tenant by another deployed app), regenerate the suffix and retry — up to 3 times. Each retry uses a fresh 4-char suffix; the kebab body stays the same.

```bash
for retry in 1 2 3; do
  # Regenerate suffix
  NEW_SUFFIX=$(LC_ALL=C tr -dc 'a-z0-9' </dev/urandom | head -c 4)
  KEBAB="${OLD_ROUTING_NAME%-*}"          # strip old suffix
  KEBAB="${KEBAB#gov-dashboard-}"         # strip prefix
  ROUTING_NAME="gov-dashboard-${KEBAB}-${NEW_SUFFIX}"

  # Re-pack and re-publish under the new routing name (the nupkg is named after -n)
  uip codedapp pack dist -n "$ROUTING_NAME" -v "$SEMVER" --output json
  uip codedapp publish --type Action -n "$ROUTING_NAME" -v "$SEMVER" --output json
  # Deploy: -n carries the friendly App name; --routing-name carries the slug.
  # --description "PINNED" only when user opted in.
  DEPLOY_CMD='uip codedapp deploy -n "$APP_NAME" --routing-name "$ROUTING_NAME" --folder-key "$FOLDER_KEY"'
  [[ "$PIN" == "yes" ]] && DEPLOY_CMD+=' --description "PINNED"'
  DEPLOY_CMD+=' --output json'
  RESP=$(eval "$DEPLOY_CMD")

  if ! echo "$RESP" | grep -qE 'routingName already exists|Routing name is already taken'; then
    # Persist the working routing name and break out
    # (atomic state.json write per state-file.md)
    break
  fi
done
```

If 3 retries fail, halt with: *"Couldn't find an available routing name after 3 attempts. Try again later or override `app.routingName` in `.dashboard/state.json` manually."*

On success, persist the new `app.routingName` to state.json so subsequent upgrades use the same value.

---

## Fresh-vs-upgrade detection

Solely from `state.json.deployment.systemName`. Not from server state, not from folder listing.

| `systemName` | Type |
|---|---|
| `null` | **Fresh** — POST `/versions/<deployVersion>/deploy` |
| non-null | **Upgrade** — PATCH `/deployed/apps/<deploymentId>` |

If the server returns `1004 "app already deployed in folder"` on a fresh attempt, auto-reconcile via `assets/scripts/discover-deployment.sh` (list deployed apps in the folder, find by routingName/title, update state.json, retry as upgrade). One-time reconciliation.

---

## `uipath.json` shape

```json
{
  "name": "<app.name from state.json — user-friendly Title Case>",
  "orgName": "<from auth-context>",
  "tenantName": "<from auth-context>",
  "baseUrl": "https://<env>.uipath.com",
  "redirectUri": "https://<org>.<env-infix>uipath.host/<routingName>"
}
```

The action subtype is communicated via `--type Action` on `uip codedapp publish`. The action-schema lives in `public/action-schema.json` (copied to `dist/` by Vite at build).

---

## Error paths

| Condition | Action |
|---|---|
| `state.json` missing | Halt: "No dashboard built here; run Build first." |
| `dist/action-schema.json` missing post-build | Halt; verify `public/action-schema.json` is present in source. |
| `dist/` missing post-build | Halt with stderr. |
| Pack: invalid name | Halt; agent regenerates routingName via intent-capture's recipe. |
| Publish: version exists | Halt; suggest semver bump; never silent-bump. |
| Publish/Deploy: HTTP 5xx or Cloudflare HTML | Auto-retry per [transient-error retry loop](#transient-error-retry-loop). |
| Deploy: routing name collision | Auto-retry up to 3× per [routing-name retry](#routing-name-retry). |
| Deploy: `1004 already deployed` on fresh attempt | Auto-reconcile via discover-deployment.sh; retry as upgrade. |
| User aborts at `Proceed?` gate | Clean exit, no side effects. |

## What Deploy does NOT do

- Scaffold (Build-only).
- Regenerate code from prompt (ships what's on disk).
- `uip codedapp push/pull` Studio Web sync (→ `uipath-coded-apps`).
- Diagnose post-deploy runtime issues (points to auth-strategy.md and stops).
