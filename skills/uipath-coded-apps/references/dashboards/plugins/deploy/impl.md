# Dashboard Deploy Plugin

Publishes a built dashboard to Automation Cloud as a Coded Web App.

**Pipeline order:** Production build → Pack → Publish → Deploy.

> **What the user should see:** The deploy plan (Step 4), progress ticks, and the final URL. All other steps are silent — run commands, read outputs in context, never echo raw JSON or bash output to the user.

---

## Pre-flight

Verify login and read state.json:

```bash
uip login status --output json
```

Check `Data.Status === "Logged in"`. If not, stop and ask the user to run `uip login`.

Read current deployment state from `.dashboard/state.json` — extract `app.name`, `app.routingName`, `app.semver`, `deployment.systemName`, `deployment.folderKey`, `deployment.folderName`.

If `routingName` is empty: tell the user to run the build first.

---

## Step 1 — Provision AdminDashboards folder (skip if folderKey already set)

If `deployment.folderKey` is already in state.json, skip this entire step.

Run the provisioning script (silent — no output to user until "AdminDashboards folder is ready"):

```bash
node "<SKILL_BASE_DIR>/assets/scripts/setup-admin-folder.mjs" "AdminDashboards" "<PROJECT_DIR>"
```

`<PROJECT_DIR>` is the dashboard project directory (e.g. `<cwd>/agent-health-x7k2`). The script reads `.dashboard/state.json` to check if already provisioned and exits immediately if so.

The script:
1. Looks up the Folder Administrator role key, the Administrators group key, and the AdminDashboards folder in parallel.
2. Creates the folder if it does not exist.
3. Reads existing role assignments before assigning — `roles assign` replaces all roles, so the script builds the full union to avoid removing existing access.
4. Persists `folderKey` and `folderName` into `.dashboard/state.json`.

> ⚠️ The script's role assignment step grants elevated folder permissions. The coding agent will ask for explicit approval — this is expected.

If the script fails with "Administrators group not found": run `uip or users list --username "Administrators" --output json` and show the user the available groups.

Tell the user: "AdminDashboards folder is ready."

---

## Step 2 — Classify deploy type

- `deployment.systemName` is empty → **Fresh deploy**
- `deployment.systemName` is set → **Upgrade**

---

## Step 3 — Bump version (silent)

```bash
node -e "
const [a,b,c] = process.argv[1].split('.').map(Number)
process.stdout.write([a, b, c + 1].join('.'))
" <CURRENT_SEMVER>
```

This gives `NEXT_SEMVER`. Don't pre-check whether it already exists — Step 7 (Publish) auto-bumps and retries on a 409 / "already exists", so a version collision self-corrects.

---

## Step 4 — Show deploy plan and ask about Governance pinning

```
Your **<APP_NAME>** is ready to be deployed.

📦  Version:    <SEMVER> → <NEXT_SEMVER>
🔗  URL path:   <ROUTING_NAME>
📁  Folder:     AdminDashboards
🔄  Type:       Fresh deploy  OR  Updating existing deployment
```

If this is a fresh deploy, also show:
```
⚠️  I'll create the AdminDashboards folder and assign Administrators as Folder Administrators.
    This requires elevated permissions — the coding agent will ask for your approval once.
```

End the deploy plan with: `Confirm to deploy, or tell me what to change.` — **pure text, no tool calls in this response. HALT.**

**On the user's reply:**
- Change request / cancel → handle it; re-present if changed
- Confirmation that already settles pinning (e.g. "deploy and pin" / "deploy without pinning") → proceed with the matching tags, ask nothing
- Bare confirmation → ask ONE short structured-choice question (SKILL.md Rule 17): *"Pin this dashboard to the Governance UI?"*

  | Option | Meaning |
  |--------|---------|
  | **Deploy and pin** | Visible in the Governance section (`--tags "governance,dashboard"`) |
  | **Deploy without pinning** | Deploy only (`--tags "governance"`) |

  Free-text replies remain valid and take precedence.

---

## Step 5 — Production build

Rename `.env.local` away before building (it may hold a dev `VITE_UIPATH_PAT`), restore after. The build still gets its SDK config from **`.env.production`** — the public config (cloud/base URL, org, tenant, client ID, scope) the build script writes. Vite loads it in production mode and the rename doesn't touch it.

```bash
node -e "const fs=require('fs'); if(fs.existsSync('.env.local')) fs.renameSync('.env.local','.env.local.bak')"
```

```bash
cd <PROJECT_DIR> && npm run build
```

```bash
node -e "const fs=require('fs'); if(fs.existsSync('.env.local.bak')) fs.renameSync('.env.local.bak','.env.local')"
```

If build fails: restore has already run. Show the error.

**Verify the SDK config is baked into the bundle** — turns the silent "UiPath SDK configuration not found" runtime crash into a build-time stop. The org name must appear in the emitted JS:

```bash
cd <PROJECT_DIR> && node -e "
const fs=require('fs'),path=require('path')
const dir='dist/assets'
const ok = fs.existsSync(dir) && fs.readdirSync(dir).some(f => f.endsWith('.js') && fs.readFileSync(path.join(dir,f),'utf8').includes(process.argv[1]))
process.stdout.write(ok ? 'CONFIG_OK' : 'CONFIG_MISSING')
" "<ORG_NAME>"
```

If it prints `CONFIG_MISSING`, `.env.production` was absent at build time — re-run the build (the build script writes it) and re-check. **Never deploy a `CONFIG_MISSING` bundle** — it loads blank in the browser.

---

## Step 6 — Pack (silent)

`-n` is the **friendly Title Case display name** (state.json `app.name`, e.g. `"Jobs Health Dashboard"`) — **never the routing slug.** The CLI sanitizes it to a slug (`jobshealthdashboard`) internally for package matching, but uses the friendly name as the display name in the catalog and Governance UI. Passing the slug makes the dashboard show up as `jobshealthdashboard`; the friendly name reads "Jobs Health Dashboard". Use the **same** `-n` for pack, publish, and deploy.

```bash
cd <PROJECT_DIR> && uip codedapp pack dist -n "<APP_NAME>" --version "<NEXT_SEMVER>" --output json
```

---

## Step 7 — Publish (silent)

```bash
cd <PROJECT_DIR> && uip codedapp publish -n "<APP_NAME>" --version "<NEXT_SEMVER>" --output json
```

Read the JSON output (silent — no output shown until success or error):
- **Success** (`Result === "Success"`)→ extract `DeploymentVersion`, continue
- **Contains "409" or "already exists"** → bump version once more, re-pack, retry publish (up to 4 attempts total)
- **Contains "5xx" or HTML** → this is a transient gateway error; wait 10 seconds and retry (up to 4 attempts)
- **Other error** → surface it to the user, stop

---

## Step 8 — Deploy

Set tags based on the user's pinning choice:
- "deploy and pin" → tags = `"governance,dashboard"`
- "deploy" → tags = `"governance"`

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

## Step 9 — Update state.json

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

## Step 10 — Report

```
🎉 **<APP_NAME>** is live.

<APP_URL>

Version <NEXT_SEMVER> · AdminDashboards
```

If pinned: "Your dashboard is now visible in the Governance section."
If not: "To pin it later, say 'redeploy and pin to governance'."

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
| state.json missing | Tell user to run the build first |

## Rules

- `-n` is the **friendly Title Case display name** (state.json `app.name`, e.g. "Jobs Health Dashboard") — same across pack, publish, deploy. Never the routing slug: the CLI slugifies it for package matching but shows the friendly name in the catalog/Governance UI.
- `--version` goes on **pack and publish only — NOT deploy.** Deploy resolves the latest published version; passing `--version` causes a false "has not been published yet" error.
- `--path-name` goes on **fresh deploy only** — it sets the URL slug. On an upgrade the routing already exists; re-passing it errors "routing name must be unique."
- Routing name is permanent after the first successful deploy.
- Always include `--tags` — minimum `governance`, add `dashboard` if the user opted to pin.
