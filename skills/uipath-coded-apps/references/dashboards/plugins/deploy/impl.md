# Dashboard Deploy Plugin

Publishes a built dashboard to Automation Cloud as a Coded Web App.

**Pipeline order:** Production build → Pack → Publish → Deploy.

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

Fire all three lookups **in one parallel message**:

```bash
uip or roles list --limit 500 --output json
```
```bash
uip or users list --username "Administrators" --output json
```
```bash
uip or folders list --all --output json
```

From the responses (read in-context — no parsing scripts needed):

**Find the Folder Administrator role key:**
Look for the entry where `Name === "Folder Administrator"`. Extract its `Key`.
If not found: stop and tell the user to check `uip or roles list --output json`.

**Find the Administrators group key:**
Look for an entry where the name is `"administrators"` (case-insensitive) and the type contains "group". Extract its `Key`.
If not found: list the available groups from the response and ask the user which group to use.

**Check if AdminDashboards folder exists:**
Look for an entry where `Name === "AdminDashboards"`. If found, extract its `Key`. If not found, create it:

```bash
uip or folders create "AdminDashboards" --output json
```

Extract the folder `Key` from the response.

**Check if role is already assigned:**

```bash
uip or roles user-roles list "Administrators" --type Group --output json
```

Look for an entry where `FolderPath === "AdminDashboards"` and `Role === "Folder Administrator"`. If found, skip assignment. If not:

> ⚠️ The next command grants elevated folder permissions. Claude Code will ask for explicit approval — this is expected.

```bash
uip or roles assign --user-key <ADMINS_GROUP_KEY> --role-keys <ROLE_KEY> --folder-key <FOLDER_KEY> --output json
```

**Persist folder key to state.json:**

```bash
node -e "
const fs   = require('fs')
const fp   = '.dashboard/state.json'
const s    = JSON.parse(fs.readFileSync(fp, 'utf8'))
s.deployment.folderKey  = process.argv[1]
s.deployment.folderName = 'AdminDashboards'
fs.writeFileSync(fp + '.tmp', JSON.stringify(s, null, 2))
fs.renameSync(fp + '.tmp', fp)
" <FOLDER_KEY>
```

Tell the user: "AdminDashboards folder is ready."

---

## Step 2 — Classify deploy type

- `deployment.systemName` is empty → **Fresh deploy**
- `deployment.systemName` is set → **Upgrade**

---

## Step 3 — Bump version

```bash
node -e "
const [a,b,c] = process.argv[1].split('.').map(Number)
process.stdout.write([a, b, c + 1].join('.'))
" <CURRENT_SEMVER>
```

This gives `NEXT_SEMVER`. Check whether this version is already published:

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

## Step 6 — Pack

`-n` is the display name — must be identical across pack, publish, and deploy:

```bash
cd <PROJECT_DIR> && uip codedapp pack dist -n "<APP_NAME>" --version "<NEXT_SEMVER>" --output json
```

---

## Step 7 — Publish

```bash
cd <PROJECT_DIR> && uip codedapp publish -n "<APP_NAME>" --version "<NEXT_SEMVER>" --output json
```

Read the JSON output:
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
  --path-name "<ROUTING_NAME>" \
  --folder-key "<FOLDER_KEY>" \
  --tags "<TAGS>" \
  --output json
```

> Note: `--version` is intentionally omitted — passing it causes "app still indexing" race errors. The CLI resolves the latest published version automatically.

Read the JSON output:
- **Success** → extract `SystemName` and `AppUrl`, continue
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
| Deploy path-name conflict | Generate new suffix, retry deploy only (pack/publish already done) |
| state.json missing | Tell user to run the build first |

## Rules

- `-n` must be the same human-readable name in pack, publish, and deploy
- `--path-name` is only in deploy — sets the URL slug
- `--version` is in pack and publish only — omit from deploy to avoid indexing race
- Routing name is permanent after first successful deploy
- Always include `--tags` — minimum `governance`, add `dashboard` if user opted to pin
