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

`<PROJECT_DIR>` is the dashboard project directory (e.g. `~/dashboards/agent-health-x7k2`). The script reads `.dashboard/state.json` to check if already provisioned and exits immediately if so.

The script:
1. Looks up the Folder Administrator role key, the Administrators group key, and the AdminDashboards folder in parallel.
2. Creates the folder if it does not exist.
3. Reads existing role assignments before assigning — `roles assign` replaces all roles, so the script builds the full union to avoid removing existing access.
4. Persists `folderKey` and `folderName` into `.dashboard/state.json`.

> ⚠️ The script's role assignment step grants elevated folder permissions. Claude Code will ask for explicit approval — this is expected.

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

This gives `NEXT_SEMVER`. Check whether this version is already published (silent):

```bash
uip codedapp list --output json
```

If an entry with `Name === "<APP_NAME>"` and `Version === "<NEXT_SEMVER>"` exists, bump once more.

---

## Step 4 — Show deploy plan and ask about Governance pinning

```
Your **<APP_NAME>** is ready to be deployed.

📦  Version:    <SEMVER> → <NEXT_SEMVER>
🔗  URL path:   <ROUTING_NAME>
📁  Folder:     AdminDashboards
🔄  Type:       Fresh deploy  OR  Updating existing deployment

📌  Do you want to pin this dashboard to the Governance UI?
   → "deploy and pin" — visible in the Governance section
   → "deploy" — deploy without pinning
```

If this is a fresh deploy, also show:
```
⚠️  I'll create the AdminDashboards folder and assign Administrators as Folder Administrators.
    This requires elevated permissions — Claude Code will ask for your approval once.
```

**HALT.** Wait for user response. Capture whether they want governance pinning.

---

## Step 5 — Production build

Protect dev credentials — rename `.env.local` before building, restore after:

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

---

## Step 6 — Pack (silent)

`-n` is the display name — must be identical across pack, publish, and deploy:

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

```bash
cd <PROJECT_DIR> && uip codedapp deploy \
  -n "<APP_NAME>" \
  --version "<NEXT_SEMVER>" \
  --path-name "<ROUTING_NAME>" \
  --folder-key "<FOLDER_KEY>" \
  --tags "<TAGS>" \
  --output json
```

Read the JSON output:
- **Success** → extract `SystemName` and `AppUrl`, continue
- **Contains "indexing" or "not been published"** → platform propagation delay after publish. Show `↻ App is indexing — retrying in 10 seconds (attempt N/3)…`. Wait 10 seconds and retry (up to 3 times). If all 3 fail, surface the error and stop.
- **Contains "conflict", "already exist", or "path" + "name"** → generate a new routing suffix and retry:

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
| Deploy "indexing" / "not been published" | Propagation delay — show retry ticker, wait 10s, retry up to 3 times |
| Deploy path-name conflict | Generate new suffix, retry deploy only (pack/publish already done) |
| state.json missing | Tell user to run the build first |

## Rules

- `-n` must be the same human-readable name in pack, publish, and deploy
- `--path-name` is only in deploy — sets the URL slug
- `--version` must match across pack, publish, and deploy
- Routing name is permanent after first successful deploy
- Always include `--tags` — minimum `governance`, add `dashboard` if user opted to pin
