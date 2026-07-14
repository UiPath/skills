# Dashboard Deploy Plugin

Publishes a built dashboard to Automation Cloud as a Coded Web App.

**Pipeline order:** Production build → Pack → Publish → Deploy.

> **What the user should see:** The deploy plan (Step 3), the mode/folder choices (Step 4), progress ticks, and the final URL. All other steps are silent — run commands, read outputs in context, never echo raw JSON or bash output to the user.

---

## Pre-flight

Verify login and read state.json:

```bash
uip login status --output json
```

Check `Data.Status === "Logged in"`. If not, stop and ask the user to run `uip login`.

Read current deployment state from `.dashboard/state.json` — extract `app.name`, `app.routingName`, `app.semver`, `deployment.systemName`, `deployment.folderKey`, `deployment.folderName`, `deployment.pinnedToGovernance`.

If `routingName` is empty: tell the user to run the build first.

---

## Step 0 — Classify deploy type

- `deployment.systemName` is empty → **Fresh deploy**
- `deployment.systemName` is set → **Upgrade** — keep the mode and folder from the prior deploy (`deployment.pinnedToGovernance` + `deployment.folderName`/`folderKey`); the plan re-confirms but Step 4 asks nothing.

---

## Step 1 — Set the publish version

The version used for pack + publish (Steps 7–8) is `NEXT_SEMVER`, derived by deploy type:

- **Fresh deploy** (`deployment.systemName` empty): first publish — use `app.semver` as-is. `NEXT_SEMVER = <CURRENT_SEMVER>` (no bump; the version doesn't exist yet).
- **Upgrade** (`deployment.systemName` set): the current version is **already published**, so you **MUST** bump before pack/publish — re-publishing the same version fails with "version already exists". This bump is mandatory, not optional; never pack/publish an upgrade at `<CURRENT_SEMVER>`. Compute the next patch:

  ```bash
  node -e "
  const [a,b,c] = process.argv[1].split('.').map(Number)
  process.stdout.write([a, b, c + 1].join('.'))
  " <CURRENT_SEMVER>
  ```

  This gives `NEXT_SEMVER`. Pack (Step 7) and Publish (Step 8) MUST pass `--version "<NEXT_SEMVER>"`.

Step 8 (Publish) still auto-bumps and retries on a 409 / "already exists" as a backstop — but on an Upgrade you bump here first; do not skip the bump and rely on the retry alone.

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
- **Standalone → Personal workspace** (zero-config, private to the user).

**Upgrade short-circuit:** if `deployment.systemName` is set, keep the state-implied mode (`deployment.pinnedToGovernance` + the tags used before) and folder (`deployment.folderName`/`folderKey`). Step 4 asks nothing.

**Capture user wording:** if the request already names a mode ("as a governance dashboard, pinned") and/or a folder ("in a new folder called X" / "to my personal workspace"), treat those as settled — the matching Step-4 question is skipped.

---

## Step 3 — Show deploy plan

`<MODE_LABEL>` / `<FOLDER_LABEL>` are the recommended (or wording-settled) values from Step 2.

```
Your **<APP_NAME>** is ready to be deployed.

📦  Version:    <SEMVER> → <NEXT_SEMVER>   (or "1.0.0 (first publish)" on a fresh deploy)
🔗  URL path:   <ROUTING_NAME>
🎯  Mode:       <MODE_LABEL>   (recommended — <why>, or "kept from last deploy" on upgrade)
📁  Folder:     <FOLDER_LABEL>   (recommended — <why>)
🔄  Type:       Fresh deploy  OR  Updating existing deployment
```

**Governance mode + fresh deploy + shared-folder target** — also show:
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

End the deploy plan with: `Confirm to deploy, or tell me what to change.` — **pure text, no tool calls in this response. HALT.**

---

## Step 4 — On confirm: settle mode, then folder

On the user's reply:
- **Change request / cancel** → handle it; re-present the plan if changed.
- **Upgrade** (`systemName` set) → skip both questions; go to Step 5 with the kept mode/folder.
- **Wording already settled both** (Step 2) → skip both; go to Step 5.

Otherwise ask up to two SHORT structured-choice questions (SKILL.md Rule 18), the recommended option first and suffixed "(Recommended)". Skip either question the wording already settled. **Never** put these in the same message as the plan — they fire only on this later, short turn.

**Question 1 — mode** (skip if settled):

| Option | Meaning |
|--------|---------|
| **Governance dashboard, pinned to Governance UI** | governance access + surfaced in the Governance section (`governance,dashboard`) |
| **Governance dashboard, not pinned** | governance access only (`governance`) |
| **Standalone coded app** | a regular dashboard app (`dashboard`) |

> ⚠️ **Pinning is a preview feature.** When offering a pinned option, state: *"Pinning surfaces the dashboard in the Governance section — an Agentic Governance preview feature, so it only takes effect if your org is enrolled in the preview. Either way the dashboard deploys and is reachable at its URL."* If the org isn't enrolled, the deploy still succeeds and the app is fully usable via its URL — only the Governance-UI pin has no visible effect until preview access is granted (contact your UiPath representative).

**Question 2 — folder** (skip if settled):

| Option | Mechanism |
|--------|-----------|
| **Personal workspace** | your own workspace, private to you |
| **Existing folder** | you provide the name |
| **Create a new folder** | you provide the name |

For a governance mode, present **`AdminDashboards`** as the recommended **Existing folder** default; "Create a new folder" covers a differently-named shared governance folder. For standalone, **Personal workspace** is recommended.

Free-text replies remain valid and take precedence.

---

## Step 5 — Resolve and provision the chosen folder

Resolve the chosen folder to `folderKey` and persist `deployment.folderKey`/`folderName` in `.dashboard/state.json`.

**If `deployment.folderKey` is already set** (upgrade / prior run) — skip this entire step.

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

## Step 6 — Production build

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

---

## Step 7 — Pack (silent)

`-n` is the **friendly Title Case display name** (state.json `app.name`, e.g. `"Jobs Health Dashboard"`) — **never the routing slug.** The CLI sanitizes it to a slug (`jobshealthdashboard`) internally for package matching, but uses the friendly name as the display name in the catalog and Governance UI. Passing the slug makes the dashboard show up as `jobshealthdashboard`; the friendly name reads "Jobs Health Dashboard". Use the **same** `-n` for pack, publish, and deploy.

```bash
cd <PROJECT_DIR> && uip codedapp pack dist -n "<APP_NAME>" --version "<NEXT_SEMVER>" --output json
```

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

## Step 8 — Publish (silent)

```bash
cd <PROJECT_DIR> && uip codedapp publish -n "<APP_NAME>" --version "<NEXT_SEMVER>" --output json
```

Read the JSON output (silent — no output shown until success or error):
- **Success** (`Result === "Success"`)→ extract `DeploymentVersion`, continue
- **Contains "409" or "already exists"** → bump version once more, re-pack, retry publish (up to 4 attempts total)
- **Contains "5xx" or HTML** → this is a transient gateway error; wait 10 seconds and retry (up to 4 attempts)
- **Other error** → surface it to the user, stop

---

## Step 9 — Deploy

Set tags from the chosen **mode** (Step 2/4):
- **Standalone** → tags = `"dashboard"`
- **Governance, pinned** → tags = `"governance,dashboard"`
- **Governance, not pinned** → tags = `"governance"`

Two flags differ from pack/publish — getting these wrong is the most common deploy failure:

- **No `--version` on deploy.** The CLI resolves the latest published version itself. Passing `--version` triggers a false `"...has not been published yet"` error.
- **`--path-name` only on a FRESH deploy.** It sets the URL slug the first time. On an **upgrade** the routing name already exists — re-passing `--path-name` errors with `"routing name must be unique"`.

**Fresh deploy** (`deployment.systemName` was empty):

```bash
cd <PROJECT_DIR> && uip codedapp deploy \
  -n "<APP_NAME>" \
  --path-name "<ROUTING_NAME>" \
  --folder-key "<FOLDER_KEY>" \
  --tags "<TAGS>" \
  --output json
```

**Upgrade** (`deployment.systemName` is set — omit `--path-name`):

```bash
cd <PROJECT_DIR> && uip codedapp deploy \
  -n "<APP_NAME>" \
  --folder-key "<FOLDER_KEY>" \
  --tags "<TAGS>" \
  --output json
```

Read the JSON output:
- **Success** → extract `SystemName` and `AppUrl`, continue
- **Contains "indexing" or "not been published"** → platform propagation delay after publish. Show `↻ App is indexing — retrying in 10 seconds (attempt N/3)…`. Wait 10 seconds and retry (up to 3 times). If all 3 fail, surface the error and stop.
- **(Fresh deploy only) Contains "conflict", "already exist", or "name must be unique"** → the routing slug is taken; generate a new suffix and retry the fresh deploy (keep `--path-name`):

```bash
node -e "
const base   = process.argv[1].replace(/-[a-z0-9]{4}$/, '')
const suffix = Math.random().toString(36).slice(2, 6)
process.stdout.write(base + '-' + suffix)
" <ROUTING_NAME>
```

Use the new routing name in a fresh deploy call. Retry up to 3 times.

- **Other error** → surface it to the user, stop

---

## Step 10 — Update state.json

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

```
🎉 **<APP_NAME>** is live.

<APP_URL>

Version <NEXT_SEMVER> · <FOLDER_NAME>
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
| Publish 409 | Auto-bump version and retry (up to 4 times) |
| Publish 5xx / HTML | Wait 10s and retry (up to 4 times) |
| Deploy "indexing" / "not been published" (with NO `--version` passed) | Propagation delay — show retry ticker, wait 10s, retry up to 3 times |
| Deploy "not been published" but you passed `--version` | Remove `--version` from the deploy call — deploy resolves the latest version itself |
| Deploy "routing name must be unique" on an upgrade | You passed `--path-name` on an upgrade — omit it; routing already exists |
| Deploy path-name conflict (fresh deploy) | Generate new suffix, retry deploy only (pack/publish already done) |
| "Agentic Governance is a preview feature and is not enabled for your organization" (on a pinned/governance deploy) | Not a deploy failure — the app IS deployed and reachable at its URL. Governance pinning is preview-gated: the pin just won't surface in the Governance section until the org is enrolled. Report success with the URL, add the preview note (Step 11), and tell the user to contact their UiPath representative for preview access. Do NOT retry or bump the version. |
| state.json missing | Tell user to run the build first |

## Rules

- `-n` is the **friendly Title Case display name** (state.json `app.name`, e.g. "Jobs Health Dashboard") — same across pack, publish, deploy. Never the routing slug: the CLI slugifies it for package matching but shows the friendly name in the catalog/Governance UI.
- `--version` goes on **pack and publish only — NOT deploy.** Deploy resolves the latest published version; passing `--version` causes a false "has not been published yet" error.
- `--path-name` goes on **fresh deploy only** — it sets the URL slug. On an upgrade the routing already exists; re-passing it errors "routing name must be unique."
- Routing name is permanent after the first successful deploy.
- Always include `--tags`, sourced from the chosen **mode**: standalone → `dashboard`; governance, not pinned → `governance`; governance, pinned → `governance,dashboard`.
- Choose **mode** and **folder** as two independent decisions (Steps 2–4). Mode sets `--tags`; only a governance mode targeting a **shared** folder provisions `setup-admin-folder.mjs` and assigns elevated roles. A Personal-workspace target never provisions roles; standalone never provisions roles.
- Recommend the mode from state.json metrics and the folder from the mode (governance→AdminDashboards, standalone→Personal workspace); the user overrides either via the Step-4 structured choice or free-text.
