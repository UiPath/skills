# Dashboard Deploy Plugin

Publishes a built dashboard to Automation Cloud as a Coded Web App.

**Order:** Build → Pack → Publish → Deploy. Each step must succeed before the next.

---

## Pre-flight

```bash
uip login status --output json
```

Check `Data.Status === "Logged in"`. If not, stop and ask the user to run `uip login`.

Read state.json:

```bash
node -e "
const fs    = require('fs')
const state = JSON.parse(fs.readFileSync('.dashboard/state.json', 'utf8'))
console.log(JSON.stringify({
  appName:     state.app?.name          ?? '',
  routingName: state.app?.routingName   ?? '',
  semver:      state.app?.semver        ?? '1.0.0',
  systemName:  state.deployment?.systemName ?? '',
  folderKey:   state.deployment?.folderKey  ?? '',
  folderName:  state.deployment?.folderName ?? '',
  appUrl:      state.deployment?.appUrl     ?? '',
}))
"
```

If `routingName` is empty — state.json is missing or the build never ran. Tell the user to run the build first.

---

## Step 1 — Provision AdminDashboards folder (idempotent, once per tenant)

All dashboards deploy to a dedicated **AdminDashboards** folder. Run this once — subsequent deploys skip it because `folderKey` will already be in state.json.

**Skip this entire step if `folderKey` is already set in state.json.**

Run the provisioning script immediately after user confirmation — no extra user prompt needed:

```bash
node "<SKILL_BASE_DIR>/assets/scripts/provision-admin-folder.mjs" "<PROJECT_DIR>"
```

This single command:
- Runs roles, users, and folder lookups **in parallel**
- Creates AdminDashboards if it doesn't exist
- Assigns Folder Administrator to the Administrators group if not already assigned
- Writes the folder key to state.json
- Is fully idempotent — safe to re-run

> **Note:** The role assignment step requires elevated permissions. Claude Code will ask for explicit approval before running it — this is expected and not a bug. Approve it once and it won't be asked again for this tenant.

After the script prints `✓ AdminDashboards ready`, read `state.json` again to get the updated `folderKey` for use in the deploy command.

Tell the user:
> "Set up the **AdminDashboards** folder and granted Administrators full access. All your dashboards will deploy here."

---

## Step 2 — Classify deploy type

- `systemName` is empty → **Fresh deploy** (first time this dashboard is deployed)
- `systemName` is set → **Upgrade** (updating an existing deployment)

---

## Step 3 — Version bump

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

📦  Version:    [SEMVER] → [NEXT_SEMVER]
🔗  URL path:   [ROUTING_NAME]
📁  Folder:     AdminDashboards
🔄  Type:       Fresh deploy  OR  Updating existing deployment

📌  Do you want to pin this dashboard to the Governance UI?
   → "deploy and pin" — visible in the Governance section
   → "deploy" — deploy without pinning

⚠️  First deploy: I'll also create the AdminDashboards folder and assign the
    Administrators group as Folder Administrator. This requires elevated permissions
    and Claude Code will ask for your explicit approval before running those commands.
```

Only show the ⚠️ note when `folderKey` is not in state.json (fresh deploy scenario).

Wait for the user's response:
- `"deploy and pin"` / `"pin"` / `"yes, pin"` → `PIN_TO_GOVERNANCE=true`
- `"deploy"` / `"yes"` / `"go ahead"` / any confirmation → `PIN_TO_GOVERNANCE=false`
- `"no"` / `"cancel"` → stop

---

## Step 5 — Production build

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

`-n` is the package display name — must match publish and deploy:

```bash
uip codedapp pack dist \
  -n "${APP_NAME}" \
  --version "${NEXT_SEMVER}" \
  --output json
```

---

## Step 7 — Publish (with transient-error retry)

```bash
TEMP_DIR=$(node -e "process.stdout.write(require('os').tmpdir())")

for ATTEMPT in 1 2 3 4; do
  uip codedapp publish \
    -n "${APP_NAME}" \
    --version "${NEXT_SEMVER}" \
    --output json > "${TEMP_DIR}/uip-publish.json" 2>&1
  PUBLISH_EXIT=$?
  PUBLISH_OUT=$(cat "${TEMP_DIR}/uip-publish.json")

  [ $PUBLISH_EXIT -eq 0 ] && break

  # 409 version conflict — bump version, re-pack, retry
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

`-n` + `--version` identify the published package (must match pack/publish). `--path-name` sets the URL slug. `--tags` controls Governance UI visibility.

**If the user opted to pin to Governance UI** (`PIN_TO_GOVERNANCE=true`):

```bash
# Note: --version is intentionally omitted — passing it causes "app still indexing"
# race errors immediately after publish. The CLI resolves the latest published version.
uip codedapp deploy \
  -n "${APP_NAME}" \
  --path-name "${ROUTING_NAME}" \
  --folder-key "${FOLDER_KEY}" \
  --tags "governance,dashboard" \
  --output json > "${TEMP_DIR}/uip-deploy.json" 2>&1
```

**If the user did not opt to pin** (`PIN_TO_GOVERNANCE=false`):

```bash
# Note: --version is intentionally omitted — passing it causes "app still indexing"
# race errors immediately after publish. The CLI resolves the latest published version.
uip codedapp deploy \
  -n "${APP_NAME}" \
  --path-name "${ROUTING_NAME}" \
  --folder-key "${FOLDER_KEY}" \
  --tags "governance" \
  --output json > "${TEMP_DIR}/uip-deploy.json" 2>&1
```

> **`-n` must be identical across pack, publish, and deploy.** `--version` is omitted from deploy — the CLI resolves the latest published version automatically, avoiding race errors immediately after publish.

Handle `--path-name` collision — package is already published, only retry deploy with a new slug:

```bash
DEPLOY_EXIT=$?
DEPLOY_OUT=$(cat "${TEMP_DIR}/uip-deploy.json")

COLLISION_ATTEMPTS=0
while echo "${DEPLOY_OUT}" | grep -qiE "conflict|already.*exist|path.*name" && [ $COLLISION_ATTEMPTS -lt 3 ]; do
  COLLISION_ATTEMPTS=$((COLLISION_ATTEMPTS + 1))
  NEW_SUFFIX=$(node -e "process.stdout.write(Math.random().toString(36).slice(2,6))")
  NEW_ROUTING=$(echo "${ROUTING_NAME}" | sed "s/-[a-z0-9]*$/-${NEW_SUFFIX}/")
  TAGS_ARG=$([ "${PIN_TO_GOVERNANCE}" = "true" ] && echo "governance,dashboard" || echo "governance")
  uip codedapp deploy \
    -n "${APP_NAME}" \
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
state.app.semver                    = process.argv[1]
state.app.routingName               = process.argv[2]
state.deployment.folderKey          = process.argv[3]
state.deployment.folderName         = 'AdminDashboards'
state.deployment.systemName         = process.argv[4] || state.deployment.systemName
state.deployment.deployVersion      = process.argv[5] || state.deployment.deployVersion
state.deployment.appUrl             = process.argv[6] || state.deployment.appUrl
state.deployment.pinnedToGovernance = process.argv[7] === 'true'
state.deployment.lastDeployedAt     = new Date().toISOString()
const tmp = fp + '.tmp'
fs.writeFileSync(tmp, JSON.stringify(state, null, 2))
fs.renameSync(tmp, fp)
process.stdout.write('state updated\n')
" "${NEXT_SEMVER}" "${ROUTING_NAME}" "${FOLDER_KEY}" \
  "${SYSTEM_NAME_NEW}" "${DEPLOY_VERSION}" "${APP_URL}" "${PIN_TO_GOVERNANCE}"
```

---

## Step 10 — Report

```
🎉 **[Dashboard Name]** is live.

[APP_URL]

Version [NEXT_SEMVER] · AdminDashboards folder
```

If pinned: "Your dashboard is now visible in the Governance section."

If not pinned: "To make it visible in the Governance UI later, say 'redeploy and pin'."

Always add: "To update after changes, say 'deploy this dashboard' again."

---

## Error handling

| Error | Action |
|-------|--------|
| "Folder Administrator" role not found | Stop — the tenant may not have standard roles. Ask the user to check `uip or roles list`. |
| "Administrators" group not found | Stop — verify the group name with `uip or users list`. |
| `uip or folders create` fails | Usually a permissions issue. User may need org-admin rights. Surface the error. |
| `uip or roles assign` fails | Same — org-admin rights required for role assignment. |
| `npm run build` fails | Fix build errors. Dev credentials are always restored. |
| Publish 409 (version conflict) | Auto-bumps version and retries. |
| Publish 5xx / HTML response | Waits and retries up to 4 times. |
| Deploy `--path-name` conflict | Regenerates URL suffix, retries deploy only (no re-pack/publish). |
| state.json missing | Tell user to run the dashboard build first. |

## Rules

- Step 1 (AdminDashboards provisioning) runs **once per tenant** — skip if `folderKey` already in state.json
- Step 1 is fully idempotent — checks before creating folder, checks before assigning role
- `-n` must be the **same value** in pack, publish, and deploy (the human-readable display name)
- `--path-name` is only in deploy — it sets the URL slug, independent of the display name
- `--version` in deploy means "deploy this already-published version" — not "create new version"
- Always include `--tags` — minimum `governance`, add `dashboard` if user opted to pin
- Routing name is permanent after first successful deploy
- PAT must not be in the production bundle — the Vite plugin enforces this
