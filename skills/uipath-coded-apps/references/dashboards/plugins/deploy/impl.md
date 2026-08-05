# Dashboard Deploy Plugin

Publishes a built dashboard to Automation Cloud as a Coded Web App.

**New-candidate order:** Build → Pack → Publish → Deploy. An exact already-published testing candidate may go directly to a reconciled upgrade without rebuilding or republishing.

> **What the user should see:** The deploy plan (Step 3), the mode/folder choices (Step 4), progress ticks, and the final URL. All other steps are silent — run commands, read outputs in context, never echo raw JSON or bash output to the user.

---

## Pre-flight inputs (deferred)

Do not run a login or cloud command merely because this file was opened. First classify the lane and present the Step 3 governed plan or testing-only execution summary. Step 4a runs the named-profile login check after the applicable authorization point.

Read current deployment state from `.dashboard/state.json` — extract `app.name`, `app.routingName`, `app.semver`, `deployment.systemName`, `deployment.folderKey`, `deployment.folderName`, `deployment.pinnedToGovernance`. These values propose a plan; they do not prove remote state.

If `routingName` is empty: tell the user to run the build first.

---

## Step 0 — Classify lane and proposed intent

Classify the release lane first:

- **Testing-only** — only when the user explicitly requests an internal, synthetic-data deployment to UiPath Alpha or Staging. Dirty source may be used, but exact built bytes/configuration are authoritative and the receipt must state `production_eligible: false` and `release_evidence: false`.
- **Governed** — Production, customer data, durable release evidence, or any ambiguity. Require reviewed source/artifact/config hashes, an approval record, immutable receipt, rollback authority, and post-deploy verification.

Then derive a **proposed** intent from local state for the plan:

- `deployment.systemName` empty → proposed **Create**
- `deployment.systemName` present → proposed **Upgrade**; tentatively keep the prior mode and folder

Do not execute from this proposal. Step 4a must prove the exact create or upgrade from fresh remote inventory. A missing local system name does not prove the app is absent; a present value does not prove that deployment still exists.

---

## Step 1 — Set the publish version

The candidate version used for pack + publish (Steps 7–8) is selected before external writes:

- **Proposed create**: propose `app.semver` as `NEXT_SEMVER`.
- **Proposed upgrade**: propose the next patch as `NEXT_SEMVER`:

  ```bash
  node -e "
  const [a,b,c] = process.argv[1].split('.').map(Number)
  process.stdout.write([a, b, c + 1].join('.'))
  " <CURRENT_SEMVER>
  ```

  This gives a proposal only. Step 4a must prove the exact candidate version is not already published before pack. If it conflicts, stop and present a revised version before any write. Never auto-bump in response to a publish failure.

---

## Step 2 — Compute recommended mode and folder (no side effects)

Two independent decisions drive the deploy: **mode** (governance treatment → tags) and **folder** (where it lands). Compute recommendations here; the user confirms/overrides in Steps 3–4.

**Mode** — three end states:

| Mode | `--tags` | Elevated role provisioning |
|------|----------|----------------------------|
| Governance dashboard, pinned to Governance UI | `governance,dashboard` | yes, on the target **shared** folder |
| Governance dashboard, not pinned | `governance` | yes, on the target **shared** folder |
| Standalone coded app | `dashboard` | none |

Recommend a mode from `.dashboard/state.json` `widgets`:
- **Governance (pinned)** when any widget's metric starts with or equals `violations-`, `agents-by-violations`, `agent-governance-violations`, `recent-violations`, `rule-evaluations-`, `rule-compliance`, `agent-compliance-report`, `policy-denials`, `governance-verdicts`.
- **Standalone** otherwise — a dashboard that happens to show agent health / jobs / KPIs is a normal app, not a governance dashboard.

**Folder** — three options: **Personal workspace** · **Existing folder** (user names it) · **Create a new folder**. Recommend:
- **Governance modes → `AdminDashboards`** (the governance home; provisioned in Step 5).
- **Standalone → an existing shared team folder such as `Shared`** (team-visible without governance role provisioning). Offer Personal workspace as the private alternative.

**Proposed-upgrade short-circuit:** if `deployment.systemName` is set, tentatively keep the state-implied mode (`deployment.pinnedToGovernance` + the tags used before) and folder (`deployment.folderName`/`folderKey`). Step 4 asks nothing unless Step 4a finds a remote discrepancy.

**Capture user wording:** if the request already names a mode ("as a governance dashboard, pinned") and/or a folder ("in a new folder called X" / "to my personal workspace"), treat those as settled — the matching Step-4 question is skipped.

---

## Step 3 — Show deploy plan

`<MODE_LABEL>` / `<FOLDER_LABEL>` are the recommended (or wording-settled) values from Step 2.

```
Your **<APP_NAME>** is ready to be deployed.

📦  Version:    <SEMVER> → <NEXT_SEMVER>   (or "1.0.0 (first publish)" on a proposed create)
🔗  URL path:   <ROUTING_NAME>
🛡️  Lane:       <TESTING_ONLY_OR_GOVERNED>
🎯  Mode:       <MODE_LABEL>   (recommended — <why>, or "kept from last deploy" on upgrade)
📁  Folder:     <FOLDER_LABEL>   (recommended — <why>)
🔄  Intent:     Proposed Create OR Upgrade — remote preflight required
```

**Governance mode + proposed create + shared-folder target** — also show:
```
⚠️  Governance deploy provisions the <FOLDER_LABEL> folder and grants Administrators
    Folder Administrator on it — an elevated permission the coding agent will ask you
    to approve once.
```
**Governance + pinned** — append:
```
    Pinning surfaces the dashboard in the Governance section, an Agentic Governance
    preview feature — effective only if your org is enrolled in the preview. Either
    way the dashboard deploys and is reachable at its URL.
```
**Standalone, or ANY Personal-workspace target** — show no elevated-permissions warning (deploying there assigns no roles).

For **governed**, end the plan with `Confirm to deploy, or tell me what to change.` — pure text, no tool calls in this response, then HALT.

For **testing-only**, the user's explicit eligible Alpha/Staging synthetic deployment request is authorization. Present the same content as an execution summary and continue without a second reply when mode and folder are already settled. If a material choice is missing, ask only that choice and wait; do not request a plan hash.

---

## Step 4 — On confirm: settle mode, then folder

On the user's reply:
- **Change request / cancel** → handle it; re-present the plan if changed.
- **Proposed upgrade** (`systemName` set) → skip both questions; go to Step 4a with the kept mode/folder.

For an already-authorized testing-only request, apply the same branches immediately after its execution summary. Ask only questions whose values were not supplied by the request.

Otherwise this is a **proposed create**: ask the two SHORT structured-choice questions below (SKILL.md Rule 18), recommended option first and suffixed "(Recommended)". **Never** put them in the same message as the plan — they fire on this later, short turn.

> **When an interactive user is present, ALWAYS present Question 1 (mode) on a proposed create.** The Step-2 inference only decides which option is pre-marked "(Recommended)" — with a human present it does **NOT** let you silently auto-pick a mode. Deploying as *standalone* without asking is a bug: an agent-health / jobs / KPI dashboard is merely *recommended* standalone, but the user may deliberately want it as a governance dashboard, so show all three and let them choose. A bare "deploy" / "confirm" / "yes" does **not** settle the mode — ask.
>
> **Skip Question 1 ONLY when:** (a) the user's wording already named the mode ("deploy as a governance dashboard, pinned" / "just deploy as a standalone app"); or (b) the user told you not to ask / to proceed without confirmation, or the run is non-interactive / automated (e.g. CI) — then use the **recommended** mode and proceed without asking (never block a headless deploy on a question). The **same two carve-outs** govern Question 2 (folder): ask when interactive, otherwise use the recommended folder.

**Question 1 — mode** (ask when a human is present; skip per carve-outs (a)/(b) above):

| Option | Meaning |
|--------|---------|
| **Governance dashboard, pinned to Governance UI** | governance access + surfaced in the Governance section (`governance,dashboard`) |
| **Governance dashboard, not pinned** | governance access only (`governance`) |
| **Standalone coded app** | a regular dashboard app (`dashboard`) |

> ⚠️ **Pinning is a preview feature.** When offering a pinned option, state: *"Pinning surfaces the dashboard in the Governance section — an Agentic Governance preview feature, so it only takes effect if your org is enrolled in the preview. Either way the dashboard deploys and is reachable at its URL."* If the org isn't enrolled, the deploy still succeeds and the app is fully usable via its URL — only the Governance-UI pin has no visible effect until preview access is granted (contact your UiPath representative).

**Question 2 — folder** (ask when a human is present; skip per carve-outs (a)/(b) above). Present these **three named options**, recommended first. **"Create a new folder" MUST appear as its own selectable option — do NOT fold it into the free-text / "type something" escape** (the escape is the separate 4th slot per Rule 18). The three are distinct *actions*, not just "type a name":

| Option | Mechanism |
|--------|-----------|
| **An existing folder** | deploy into a folder that already exists; resolve its key by name. Offer a **concrete** default, not the generic word "existing": **`AdminDashboards`** for a governance mode, or a shared team folder (e.g. **`Shared`**) for standalone. The user may name a different existing folder in free text. |
| **Create a new folder** | the user gives a name; you run `uip or folders create` (governance shared folder → provision via `setup-admin-folder.mjs`) and deploy into it |
| **Personal workspace** | your own workspace, private to you |

Recommended (first, suffixed "(Recommended)"): the existing-folder default — **`AdminDashboards`** for a governance mode; a shared team folder (e.g. `Shared`) for a standalone dashboard (a dashboard is usually team-facing; offer Personal workspace as the private alternative).

Free-text replies (including a bare folder name) remain valid and take precedence.

---

## Step 4a — Prove the remote operation (read-only)

Verify the exact named profile first:

```bash
uip login status --profile "<CLI_PROFILE>" --output json
```

Check `Data.Status === "Logged in"`. If not, stop and ask the user to authenticate that profile. Bind its control plane, org, and tenant; do not reuse a default session whose target is ambiguous.

Before folder provisioning, publish, or deploy, query the authenticated target's authoritative app/package inventory through an approved inventory-capable deployment helper or Apps API runtime. The stock `uip codedapp` 1.198.0 surface exposes `init`, `pack`, `publish`, `deploy`, `push`, and `pull`, but no deployment `list`/`get`; it cannot satisfy this preflight by itself. Never obtain or print a bearer token to compensate. If no approved inventory-capable path is available, stop; local files are not an acceptable fallback.

Bind and compare the exact control plane, org, tenant, named profile, app/package name, OAuth client, intended route, folder, current deployment/system identity, current version, candidate version, and app type.

- **Create** passes only when there is no matching deployment and the exact route is unused.
- **Upgrade** passes only when one exact existing deployment matches the local candidate's system identity, permanent route, folder, client, and current version.
- The candidate version must be the exact reviewed version and must not already exist before a new publish.
- Testing-only additionally requires Alpha or Staging, internal authentication, and synthetic data. Otherwise stop or reclassify as governed.

If authoritative evidence changes the proposed intent, mode, folder, route, current version, or candidate version, re-present the corrected plan and wait for confirmation—even in testing-only. Never silently switch create↔upgrade.

Start the lane's receipt before the first external write. A testing-only run creates its automatic receipt without a second hash approval. A governed run requires its reviewed approval and immutable receipt first.

---

## Step 5 — Resolve and provision the chosen folder

Resolve the chosen folder to `folderKey` and persist `deployment.folderKey`/`folderName` in `.dashboard/state.json`.

After authorization, confirm the Orchestrator tool prerequisite:

```bash
uip tools list --output json
# Only when the returned inventory lacks orchestrator-tool:
uip tools install @uipath/orchestrator-tool
```

This is the only `uip tools list` use permitted by the dashboard capability. If installation fails, stop before folder operations rather than improvising a portal path.

**If Step 4a verified the existing deployment's exact `folderKey`** (upgrade) — skip this entire step. A local folder key alone is insufficient.

**Governance mode targeting a SHARED folder** (AdminDashboards, or any user-named/newly-created shared folder — anything except Personal workspace) — provision via the script (silent — no output to user until "<FOLDER_NAME> folder is ready"):

```bash
node "<SKILL_BASE_DIR>/assets/scripts/dashboards/setup-admin-folder.mjs" "<FOLDER_NAME>" "<PROJECT_DIR>"
```

`<FOLDER_NAME>` is the chosen governance folder (`AdminDashboards` by default). `<PROJECT_DIR>` is the dashboard project directory (e.g. `<cwd>/agent-health-x7k2`). The script reads `.dashboard/state.json`, exits immediately if already provisioned, else:

1. Looks up the Folder Administrator role key, the Administrators group key, and the folder in parallel.
2. Creates the folder if it does not exist.
3. Reads existing role assignments before assigning — `roles assign` replaces all roles, so the script builds the full union to avoid removing existing access.
4. Persists `folderKey` and `folderName` into `.dashboard/state.json`.

> ⚠️ The script's role assignment step grants elevated folder permissions. The coding agent will ask for explicit approval — this is expected.

If the script fails with "Administrators group not found": run `uip or users list --username "Administrators" --output json` and show the user the available groups.

Tell the user: "<FOLDER_NAME> folder is ready."

**Personal workspace** (any mode) — resolve, no provisioning:

```bash
uip or folders list --output json
```

Pick the `Data[]` row where `Type == "Personal"`, read its `Key`. Persist `folderKey`/`folderName`. No folder is created and no roles are assigned — a governance dashboard in a personal workspace needs no role provisioning, since the owner already has full access. If no `Personal` row is found, show the folder list and ask the user to pick another option.

**Existing folder by name** (standalone) — resolve per SKILL.md Rule 11:

```bash
uip or folders list --output json
```

Match on `Name`, read `Key`. Persist.

**Create a new folder** (standalone) —

```bash
uip or folders create "<FOLDER_NAME>" --output json
```

Capture `Data.Key`. If it fails "already exists," resolve the existing folder's key from `uip or folders list` instead. Persist.

---

## Step 6 — Build or bind the candidate

For a source-built candidate:

```bash
cd <PROJECT_DIR> && npm run build
```

If build fails: show the error.

No `.env` dance — the SDK config lives in `uipath.json`. The `uipathCodedApps()` Vite plugin reads it and injects `<meta name="uipath:*">` tags into `dist/index.html` at build time; the SDK (`new UiPath()`) reads its config from those tags at runtime. No tokens are baked into the bundle.

**Verify the SDK config is injected into the built `index.html`** — turns the silent "UiPath SDK configuration not found" runtime crash into a build-time stop. The org-name meta tag must appear:

```bash
cd <PROJECT_DIR> && node -e "
const fs=require('fs')
const html = fs.existsSync('dist/index.html') ? fs.readFileSync('dist/index.html','utf8') : ''
process.stdout.write(html.includes('uipath:org-name') ? 'CONFIG_OK' : 'CONFIG_MISSING')
"
```

If it prints `CONFIG_MISSING`, `uipath.json` lacked `orgName` at build time — re-run the build (the build script writes `uipath.json`) and re-check. **Never deploy a `CONFIG_MISSING` bundle** — it loads blank in the browser. **Skip this check for template builds** (Step 7b) — a tenant-neutral template intentionally omits the org name.

For an explicitly requested testing-only "deploy as-is" operation, an existing `dist/` or exact already-published candidate may be used without rebuilding. Hash and audit the exact bytes and runtime configuration, record the skipped build in the automatic testing receipt, and never claim source provenance or production readiness. If the candidate is already published and Step 4a identified it exactly, skip Steps 7–8; do not repack or republish it.

---

## Step 7 — Pack (silent)

`-n` is the **friendly Title Case display name** (state.json `app.name`, e.g. `"Jobs Health Dashboard"`) — **never the routing slug.** The CLI sanitizes it to a slug (`jobshealthdashboard`) internally for package matching, but uses the friendly name as the display name in the catalog and Governance UI. Passing the slug makes the dashboard show up as `jobshealthdashboard`; the friendly name reads "Jobs Health Dashboard". Use the **same** `-n` for pack, publish, and deploy.

```bash
cd <PROJECT_DIR> && uip codedapp pack dist -n "<APP_NAME>" --version "<NEXT_SEMVER>" -o .uipath
```

Verify and hash the resulting `.nupkg` directly. `pack` uses `--output` for its output directory, so do not pass `--output json` to this subcommand.

---

### Step 7b — Template packaging (only when shipping a reusable template)

A **template** is a dashboard distributed in the ejected regime: one artifact carrying both the deploy face (`dist/`) and the agent-modifiable source. Before `pack`, stage the source + manifest into `dist/_source/`:

```bash
cd <PROJECT_DIR> && node "${SKILL_BASE_DIR}/assets/scripts/dashboards/build-dashboard.mjs" --pack-template <PROJECT_DIR>
```

This stages a **tenant-neutral** modify-face (`intent.json`, `src/`, config files, `uipath.json` with tenant identity blanked — only `scope` retained) plus `template.json` (scaffoldVersion, sdkFloor, requiredScopes, routingName, `ejected: true`) into `dist/_source/`, then emits `TEMPLATE_PACKED` with the `pack` command. It never stages `.dashboard/`, `node_modules`, or `dist`. Run the normal `pack` (above) afterward.

> **Caveat — `dist/_source/*` is web-served.** The platform serves `dist`, so embedded source is publicly fetchable at the app URL. Ship it ONLY for shareable, tenant-neutral templates — never a customer's private dashboard.

**Tenant-neutral runtime config.** A template build (`intent.template: true`) writes a scope-only `uipath.json` (no org/tenant/base-url/client-id), so the plugin injects only the `uipath:scope` meta tag — **no** tenant identity is baked into the bundle. At runtime the UiPath Apps host injects the remaining `<meta name="uipath:*">` config tags (org/tenant/base-url/client-id) and loads the app with `?host=embed`; the scaffold's `useAuth` calls `new UiPath()`, which reads that config and delegates the token to the host. So the same bundle is portable across tenants.

> **Skip the CONFIG_OK check (Step 6) for template builds.** That check greps `dist/index.html` for the org-name meta tag, which a tenant-neutral template intentionally omits — it would false-fail. Config arrives from host-injected meta tags at runtime instead.

---

## Step 8 — Publish once (silent)

```bash
cd <PROJECT_DIR> && uip codedapp publish \
  -n "<APP_NAME>" \
  --version "<NEXT_SEMVER>" \
  --profile "<CLI_PROFILE>" \
  --output json
```

Read the JSON output (silent — no output shown until success or error):
- **Success** (`Result === "Success"`) → extract `DeploymentVersion`. Poll authoritative read-only inventory until that exact candidate is visible/indexed, then continue.
- **Any non-success, timeout, interruption, 409, 5xx, or HTML response** → mark the write indeterminate, stop this operation, and reconcile remote package/app state. Do not auto-bump, repack, or retry in the same run.

---

## Step 9 — Deploy

Set tags from the chosen **mode** (Step 2/4):
- **Standalone** → tags = `"dashboard"`
- **Governance, pinned** → tags = `"governance,dashboard"`
- **Governance, not pinned** → tags = `"governance"`

Bind the exact candidate and target:

- **Always pass `--version <NEXT_SEMVER>`.** Wait for authoritative inventory to show that exact candidate before deploy. Never omit it merely to select an unreviewed Latest version.
- **Pass `--path-name` only on a proven Create.** It permanently sets the URL route.
- **Omit `--path-name` on a proven Upgrade.** Preserve and verify the existing route.
- Pass the exact non-confidential OAuth client from the audited runtime configuration and the named authenticated profile.

**Create** (proved by Step 4a):

```bash
cd <PROJECT_DIR> && uip codedapp deploy \
  -n "<APP_NAME>" \
  --version "<NEXT_SEMVER>" \
  --path-name "<ROUTING_NAME>" \
  --client-id "<CLIENT_ID>" \
  --folder-key "<FOLDER_KEY>" \
  --tags "<TAGS>" \
  --profile "<CLI_PROFILE>" \
  --output json
```

**Upgrade** (proved by Step 4a; omit `--path-name`):

```bash
cd <PROJECT_DIR> && uip codedapp deploy \
  -n "<APP_NAME>" \
  --version "<NEXT_SEMVER>" \
  --client-id "<CLIENT_ID>" \
  --folder-key "<FOLDER_KEY>" \
  --tags "<TAGS>" \
  --profile "<CLI_PROFILE>" \
  --output json
```

Read the JSON output:
- **Success** → extract `SystemName` and `AppUrl`, then continue to authoritative post-verification.
- **Any non-success, timeout, interruption, indexing error, conflict, 5xx, HTML response, or `routing name must be unique`** → mark the write indeterminate, stop this operation, and reconcile the exact remote deployment/version/route. Never retry with a random route, omitted route, omitted version, delete/recreate, or create fallback.

---

## Step 10 — Verify remotely, then update state.json

Re-read the authoritative deployment before writing local state. Require the exact org, tenant, folder, deployment/system identity, version, route, client, tags, and URL from Steps 4a and 9. Verify the route and referenced assets, authentication, and an app-specific smoke test. If verification fails, leave local state unchanged and record `deployed_unverified` (testing) or the governed failure state.

Only after all checks pass, update `.dashboard/state.json` atomically:

```bash
node -e "
const fs = require('fs')
const fp = '.dashboard/state.json'
const s  = JSON.parse(fs.readFileSync(fp, 'utf8'))
s.app.semver                    = process.argv[1]
s.app.routingName               = process.argv[2]
s.deployment.systemName         = process.argv[3] || s.deployment.systemName
s.deployment.deployVersion      = process.argv[4] || s.deployment.deployVersion
s.deployment.appUrl             = process.argv[5] || s.deployment.appUrl
s.deployment.pinnedToGovernance = process.argv[6] === 'true'
s.deployment.lastDeployedAt     = new Date().toISOString()
fs.writeFileSync(fp + '.tmp', JSON.stringify(s, null, 2))
fs.renameSync(fp + '.tmp', fp)
" <NEXT_SEMVER> <ROUTING_NAME> <SYSTEM_NAME> <DEPLOY_VERSION> <APP_URL> <PIN_TO_GOVERNANCE>
```

---

## Step 11 — Report

For a governed release that passed every acceptance check:

```
🎉 **<APP_NAME>** is live.

<APP_URL>

Version <NEXT_SEMVER> · <FOLDER_NAME>
```

For testing-only:

```
**<APP_NAME>** is deployed for synthetic Alpha/Staging testing.

<APP_URL>

Version <NEXT_SEMVER> · <FOLDER_NAME> · Not production eligible
```

**(governance only)**
- If pinned: "Your dashboard is pinned to the Governance section. Note: the Governance section is an **Agentic Governance preview** feature — if your org isn't enrolled in the preview, the pin won't appear there yet (contact your UiPath representative for access). The dashboard is live and fully usable at the URL above regardless."
- If not: "To pin it later, say 'redeploy and pin to governance'."

Always: "To update after making changes, say 'deploy this dashboard' again."

---

## Error reference

| Situation | What to do |
|-----------|-----------|
| "Folder Administrator" role not found | Run `uip or roles list --output json` and show the user the available roles |
| Administrators group not found | List groups from the response, ask user which to use |
| Build fails | Show the error — dev credentials are always restored |
| Publish 409 / version exists | Stop and reconcile whether the exact publish occurred. Select a different version only in a new reviewed operation; never auto-bump. |
| Publish/deploy timeout, interruption, 5xx, HTML, or nonzero exit | Treat the external write as indeterminate; reconcile remote state and stop the current operation. |
| Candidate is not indexed | Poll authoritative read-only inventory before deploy. Do not issue and retry a deploy while indexing is unresolved. |
| Deploy `routing name must be unique` on upgrade | Stop and reconcile the exact deployment target. Omit `--path-name` only in a fresh, proved upgrade operation; never blind-retry. |
| Deploy route conflict on create | Stop and present an intentional plan change. Never generate a suffix or omit the reviewed route. |
| "Agentic Governance is a preview feature and is not enabled for your organization" (on a pinned/governance deploy) | Not a deploy failure — the app IS deployed and reachable at its URL. Governance pinning is preview-gated: the pin just won't surface in the Governance section until the org is enrolled. Report success with the URL, add the preview note (Step 11), and tell the user to contact their UiPath representative for preview access. Do NOT retry or bump the version. |
| state.json missing | Tell user to run the build first |

## Rules

- `-n` is the **friendly Title Case display name** (state.json `app.name`, e.g. "Jobs Health Dashboard") — same across pack, publish, deploy. Never the routing slug: the CLI slugifies it for package matching but shows the friendly name in the catalog/Governance UI.
- `--version` goes on pack, publish, and deploy so the exact candidate stays bound. Prove it is indexed before deploy; never omit it to select Latest.
- `--path-name` goes on a remotely proved Create only. Omit it on a remotely proved Upgrade while preserving and post-verifying the existing route.
- Routing name is permanent after the first successful deploy.
- `.dashboard/state.json` and `.uipath/app.config.json` are repairable projections, not remote authority.
- Never auto-upsert, auto-bump, randomize a route, omit a reviewed route/version, delete/recreate, or blind-retry an indeterminate external write.
- Testing-only is explicit, internal, synthetic, and limited to Alpha/Staging with an automatic non-production receipt. All other deployments default to governed.
- Always include `--tags`, sourced from the chosen **mode**: standalone → `dashboard`; governance, not pinned → `governance`; governance, pinned → `governance,dashboard`.
- Choose **mode** and **folder** as two independent decisions (Steps 2–4). Mode sets `--tags`; only a governance mode targeting a **shared** folder provisions `setup-admin-folder.mjs` and assigns elevated roles. A Personal-workspace target never provisions roles; standalone never provisions roles.
- Recommend the mode from state.json metrics and the folder from the mode (governance→AdminDashboards, standalone→an existing shared team folder such as `Shared`); offer Personal workspace as the private alternative. The user overrides either via the Step-4 structured choice or free-text.
