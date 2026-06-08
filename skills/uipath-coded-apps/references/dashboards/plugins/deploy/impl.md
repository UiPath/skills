# Dashboard Deploy Plugin

Publishes a built dashboard to Automation Cloud as a Coded Web App.

**Order:** Build → Pack → Publish → Deploy. Each step must succeed before the next.

---

## Pre-flight

```bash
# Verify login
uip login status --output json
```

Check `Data.Status === "Logged in"`. If not, stop and ask the user to run `uip login`.

Read state.json:

```bash
node -e "
const fs   = require('fs')
const state = JSON.parse(fs.readFileSync('.dashboard/state.json', 'utf8'))
console.log(JSON.stringify({
  appName:    state.app?.name       ?? '',
  routingName: state.app?.routingName ?? '',
  semver:     state.app?.semver     ?? '1.0.0',
  systemName: state.deployment?.systemName ?? '',
  folderKey:  state.deployment?.folderKey  ?? '',
  folderName: state.deployment?.folderName ?? '',
  appUrl:     state.deployment?.appUrl     ?? '',
}))
"
```

If `routingName` is empty — state.json is missing or the build never ran. Tell the user to run the build first.

---

## Step 1 — Classify deploy type

- `systemName` is empty → **Fresh deploy** (first time)
- `systemName` is set → **Upgrade** (update existing deployment, folder already known)

For upgrades, skip Step 2 (folder is already in state.json).

---

## Step 2 — Resolve folder (fresh deploy only)

List all folders:

```bash
TEMP_DIR=$(node -e "process.stdout.write(require('os').tmpdir())")
uip or folders list --all --output json > "${TEMP_DIR}/uip-folders.json"
```

Check if "Shared" folder exists:

```bash
node -e "
const folders = JSON.parse(require('fs').readFileSync(process.argv[1], 'utf8'))
const shared  = folders.find(f => f.Name === 'Shared' || f.DisplayName === 'Shared')
process.stdout.write(shared ? JSON.stringify({ key: shared.Key, name: shared.Name }) : 'NONE')
" "${TEMP_DIR}/uip-folders.json"
```

**If "Shared" exists:** use it automatically. Record `FOLDER_KEY` and `FOLDER_NAME = "Shared"`. No user prompt needed for the folder.

**If "Shared" does not exist:** read the folder list and suggest the top options to the user:

```bash
node -e "
const folders = JSON.parse(require('fs').readFileSync(process.argv[1], 'utf8'))
const top = folders
  .filter(f => f.Name && !f.Name.startsWith('_'))
  .sort((a, b) => a.Name.localeCompare(b.Name))
  .slice(0, 6)
  .map(f => f.Name)
process.stdout.write(top.join('\n'))
" "${TEMP_DIR}/uip-folders.json"
```

Ask the user:

> "There's no 'Shared' folder in this tenant. Which folder should the dashboard live in?
> [list the top options above]
> Or type a different folder name."

Once the user confirms a folder name, look up its key:

```bash
FOLDER_KEY=$(node -e "
const folders = JSON.parse(require('fs').readFileSync(process.argv[1], 'utf8'))
const match   = folders.find(f => f.Name === process.argv[2])
if (!match) { process.stderr.write('Folder not found\n'); process.exit(1) }
process.stdout.write(match.Key)
" "${TEMP_DIR}/uip-folders.json" "<FOLDER_NAME>")
rm -f "${TEMP_DIR}/uip-folders.json"
```

---

## Step 3 — Bump version

```bash
NEXT_SEMVER=$(node -e "
const [major, minor, patch] = process.argv[1].split('.').map(Number)
process.stdout.write([major, minor, patch + 1].join('.'))
" "${SEMVER}")
```

Version conflict check — avoid a 409 on publish:

```bash
TEMP_DIR=$(node -e "process.stdout.write(require('os').tmpdir())")
uip codedapp list --output json > "${TEMP_DIR}/uip-apps.json" 2>/dev/null
EXISTING=$(node -e "
try {
  const apps = JSON.parse(require('fs').readFileSync(process.argv[1], 'utf8'))
  const hit  = apps.find(p => p.Name === process.argv[2] && p.Version === process.argv[3])
  process.stdout.write(hit ? 'EXISTS' : 'OK')
} catch { process.stdout.write('SKIP') }
" "${TEMP_DIR}/uip-apps.json" "${APP_NAME}" "${NEXT_SEMVER}")
rm -f "${TEMP_DIR}/uip-apps.json"
if [ "${EXISTING}" = "EXISTS" ]; then
  NEXT_SEMVER=$(node -e "
  const [a,b,c] = process.argv[1].split('.').map(Number)
  process.stdout.write([a, b, c + 1].join('.'))
  " "${NEXT_SEMVER}")
fi
```

---

## Step 4 — Show deploy plan and ask about Governance pinning

Present this to the user:

```
Your **[Dashboard Name]** is ready to be deployed.

📦  Version:   [SEMVER] → [NEXT_SEMVER]
🔗  URL path:  [ROUTING_NAME]
📁  Folder:    [FOLDER_NAME]
🔄  Type:      Fresh deploy  OR  Updating existing deployment

📌  Do you want to pin this dashboard to the Governance UI?

   → Say **"deploy and pin"** to make it visible in the Governance section
   → Say **"deploy"** (or just **"yes"**) to deploy without pinning
```

Wait for the user's response:
- `"deploy and pin"` / `"pin"` / `"yes, pin"` → set `PIN_TO_GOVERNANCE=true`
- `"deploy"` / `"yes"` / `"go ahead"` / any other confirmation → set `PIN_TO_GOVERNANCE=false`
- `"no"` / `"cancel"` → stop

---

## Step 5 — Production build

Temporarily move `.env.local` so dev credentials don't enter the production bundle. Restore it regardless of success or failure:

```bash
cd <PROJECT_DIR>
[ -f .env.local ] && mv .env.local .env.local.deploy-bak
npm run build
BUILD_EXIT=$?
[ -f .env.local.deploy-bak ] && mv .env.local.deploy-bak .env.local
[ $BUILD_EXIT -ne 0 ] && echo "Build failed — credentials restored" && exit 1
```

---

## Step 6 — Pack

`-n` is the package display name. Must be the same value used in publish and deploy:

```bash
uip codedapp pack dist \
  -n "${APP_NAME}" \
  --version "${NEXT_SEMVER}" \
  --output json
```

---

## Step 7 — Publish (with transient-error retry)

`-n` and `--version` select the exact package to upload — must match what was packed:

```bash
TEMP_DIR=$(node -e "process.stdout.write(require('os').tmpdir())")

for ATTEMPT in 1 2 3 4; do
  uip codedapp publish \
    -n "${APP_NAME}" \
    --version "${NEXT_SEMVER}" \
    --output json > "${TEMP_DIR}/uip-publish.json" 2>&1
  PUBLISH_EXIT=$?
  PUBLISH_OUT=$(cat "${TEMP_DIR}/uip-publish.json")

  # Success
  [ $PUBLISH_EXIT -eq 0 ] && break

  # 409 version conflict — bump version, re-pack, and retry publish
  if echo "${PUBLISH_OUT}" | grep -q "409\|already exists"; then
    NEXT_SEMVER=$(node -e "
    const [a,b,c] = process.argv[1].split('.').map(Number)
    process.stdout.write([a, b, c + 1].join('.'))
    " "${NEXT_SEMVER}")
    uip codedapp pack dist -n "${APP_NAME}" --version "${NEXT_SEMVER}" --output json
    continue
  fi

  # Transient gateway error — wait and retry
  if echo "${PUBLISH_OUT}" | grep -qE "5[0-9]{2}|<!DOCTYPE|<html"; then
    sleep $((ATTEMPT * 5))
    continue
  fi

  echo "Publish failed: ${PUBLISH_OUT}" && exit 1
done
[ $PUBLISH_EXIT -ne 0 ] && echo "Publish failed after 4 attempts" && exit 1

DEPLOY_VERSION=$(node -e "
try {
  const d = JSON.parse(process.argv[1])
  process.stdout.write(String(d.DeploymentVersion || d.deploymentVersion || ''))
} catch { process.stdout.write('') }
" "${PUBLISH_OUT}")
rm -f "${TEMP_DIR}/uip-publish.json"
```

---

## Step 8 — Deploy

`-n`, `--version` identify the published package. `--path-name` sets the URL slug. `--tags` controls Governance UI visibility.

**All three of `-n`, `--version`, `-n` must match the values used in pack and publish.**

**If the user opted to pin to Governance UI** (`PIN_TO_GOVERNANCE=true`):

```bash
uip codedapp deploy \
  -n "${APP_NAME}" \
  --version "${NEXT_SEMVER}" \
  --path-name "${ROUTING_NAME}" \
  --folder-key "${FOLDER_KEY}" \
  --tags "governance,dashboard" \
  --output json > "${TEMP_DIR}/uip-deploy.json" 2>&1
```

**If the user did not opt to pin** (`PIN_TO_GOVERNANCE=false`):

```bash
uip codedapp deploy \
  -n "${APP_NAME}" \
  --version "${NEXT_SEMVER}" \
  --path-name "${ROUTING_NAME}" \
  --folder-key "${FOLDER_KEY}" \
  --tags "governance" \
  --output json > "${TEMP_DIR}/uip-deploy.json" 2>&1
```

> **`-n` and `--version` must be the same across pack, publish, and deploy.** Pack creates the package. Publish uploads it by name+version. Deploy resolves the published app by name+version and sets the URL path via `--path-name`.
>
> Note: `--version` in deploy means "deploy this already-published version" — it does not create a new version.

Handle `--path-name` collision — the package is already published, only the deploy needs to retry with a new slug:

```bash
DEPLOY_EXIT=$?
DEPLOY_OUT=$(cat "${TEMP_DIR}/uip-deploy.json")

COLLISION_ATTEMPTS=0
while echo "${DEPLOY_OUT}" | grep -qiE "conflict|already.*exist|path.*name" && [ $COLLISION_ATTEMPTS -lt 3 ]; do
  COLLISION_ATTEMPTS=$((COLLISION_ATTEMPTS + 1))
  NEW_SUFFIX=$(node -e "process.stdout.write(Math.random().toString(36).slice(2,6))")
  NEW_ROUTING=$(echo "${ROUTING_NAME}" | sed "s/-[a-z0-9]*$/-${NEW_SUFFIX}/")
  TAGS_ARG=$([ "${PIN_TO_GOVERNANCE}" = "true" ] && echo "governance,dashboard" || echo "governance")
  # No re-pack or re-publish needed — package is already uploaded, only path-name changes
  uip codedapp deploy \
    -n "${APP_NAME}" \
    --version "${NEXT_SEMVER}" \
    --path-name "${NEW_ROUTING}" \
    --folder-key "${FOLDER_KEY}" \
    --tags "${TAGS_ARG}" \
    --output json > "${TEMP_DIR}/uip-deploy.json" 2>&1
  DEPLOY_EXIT=$?
  DEPLOY_OUT=$(cat "${TEMP_DIR}/uip-deploy.json")
  [ $DEPLOY_EXIT -eq 0 ] && ROUTING_NAME="${NEW_ROUTING}" && break
done

[ $DEPLOY_EXIT -ne 0 ] && echo "Deploy failed: ${DEPLOY_OUT}" && exit 1

SYSTEM_NAME_NEW=$(node -e "
try { const d=JSON.parse(process.argv[1]); process.stdout.write(d.SystemName||d.systemName||'') }
catch { process.stdout.write('') }
" "${DEPLOY_OUT}")
APP_URL=$(node -e "
try { const d=JSON.parse(process.argv[1]); process.stdout.write(d.AppUrl||d.appUrl||'') }
catch { process.stdout.write('') }
" "${DEPLOY_OUT}")
rm -f "${TEMP_DIR}/uip-deploy.json"
```

---

## Step 9 — Update state.json

```bash
node -e "
const fs    = require('fs')
const path  = require('path')
const fp    = path.join('.dashboard', 'state.json')
const state = JSON.parse(fs.readFileSync(fp, 'utf8'))
state.app.semver              = process.argv[1]
state.app.routingName         = process.argv[2]
state.deployment.folderKey    = process.argv[3]
state.deployment.folderName   = process.argv[4]
state.deployment.systemName   = process.argv[5] || state.deployment.systemName
state.deployment.deployVersion = process.argv[6] || state.deployment.deployVersion
state.deployment.appUrl       = process.argv[7] || state.deployment.appUrl
state.deployment.pinnedToGovernance = process.argv[8] === 'true'
state.deployment.lastDeployedAt = new Date().toISOString()
const tmp = fp + '.tmp'
fs.writeFileSync(tmp, JSON.stringify(state, null, 2))
fs.renameSync(tmp, fp)
process.stdout.write('state updated\n')
" "${NEXT_SEMVER}" "${ROUTING_NAME}" "${FOLDER_KEY}" "${FOLDER_NAME}" \
  "${SYSTEM_NAME_NEW}" "${DEPLOY_VERSION}" "${APP_URL}" "${PIN_TO_GOVERNANCE}"
```

---

## Step 10 — Report

```
🎉 **[Dashboard Name]** is live.

[APP_URL]

Version [NEXT_SEMVER] · Folder: [FOLDER_NAME]
```

If pinned to Governance UI:
> "Your dashboard is now visible in the Governance section. To unpin it later, say 'redeploy without governance pin'."

If not pinned:
> "To make it visible in the Governance UI later, say 'redeploy and pin to governance'."

Add in both cases:
> "To update the dashboard after making changes, say 'deploy this dashboard' again."

---

## Error handling

| Error | Action |
|-------|--------|
| `npm run build` fails | Fix build errors first. Dev credentials are always restored. |
| `uip codedapp pack` fails | Verify `dist/` exists — run `npm run build` first. |
| Publish 409 (version conflict) | Auto-bumps version and retries. |
| Publish 5xx / HTML response | Waits and retries up to 4 times. |
| Deploy `--path-name` conflict | Regenerates URL suffix and retries up to 3 times. |
| Folder key not found | Re-run `uip or folders list --all --output json` and verify the folder name. |
| state.json missing | Tell user to run the dashboard build first. |

## Rules

- Pack order is always: **build → pack → publish → deploy**
- `--path-name` in the deploy command takes the routing slug (e.g. `agent-health-x7k2`)
- `-n` must be the **same value** in pack, publish, and deploy — it is the package identity that threads the pipeline together. Use the human-readable dashboard name from state.json (e.g. `"Agent Health Dashboard"`) — no sanitization, no modification
- `--path-name` takes the **routing slug** (e.g. `"agent-health-x7k2"`) — only in the deploy command, sets the URL path
- Always include `--tags` — minimum is `governance`, add `dashboard` if user opted to pin
- Routing name is permanent after first successful deploy — never change it
- PAT must not be in the production bundle — the Vite plugin enforces this
- Default folder is "Shared" if it exists; otherwise present options from the folder list
