# Dashboard Deploy Plugin

Deploys a built dashboard to Automation Cloud as a Coded Web App.

## Pre-flight

```bash
# 1. Verify login
uip login status --output json   # must show Data.Status == "Logged in"

# 2. Read state.json (must exist — run build first if missing)
STATE=$(cat .dashboard/state.json 2>/dev/null || echo '{}')
APP_NAME=$(node -e "const s=JSON.parse(process.argv[1]); process.stdout.write(s.app?.name||'')" "$STATE")
ROUTING_NAME=$(node -e "const s=JSON.parse(process.argv[1]); process.stdout.write(s.app?.routingName||'')" "$STATE")
SEMVER=$(node -e "const s=JSON.parse(process.argv[1]); process.stdout.write(s.app?.semver||'1.0.0')" "$STATE")
SYSTEM_NAME=$(node -e "const s=JSON.parse(process.argv[1]); process.stdout.write(s.deployment?.systemName||'')" "$STATE")
FOLDER_KEY=$(node -e "const s=JSON.parse(process.argv[1]); process.stdout.write(s.deployment?.folderKey||'')" "$STATE")

# 3. Sanitize display name for the deploy command.
# The CLI strips special chars from -n before matching the published package.
# "Agent Health & Traceview" → "agenthealthtraceview" (no hyphens!) which won't
# match the routing slug "agent-health-traceview". Sanitize the same way we built
# the routing name: lowercase + hyphens only.
APP_SAFE_NAME=$(node -e "
  const n = process.argv[1];
  process.stdout.write(n.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/(^-|-$)/g,''));
" "$APP_NAME")
```

If `ROUTING_NAME` is empty → state.json is missing or corrupt. Tell user to run the build first.

## Step 1 — Classify deploy type

- `SYSTEM_NAME` empty → **Fresh deploy** (first time this dashboard is deployed)
- `SYSTEM_NAME` non-empty → **Upgrade deploy** (update existing deployment)

## Step 2 — Resolve folder key

If `FOLDER_KEY` is empty (fresh deploy or folder lost):

```bash
# --all is required — without it the list is capped at 50 and may miss folders
# Write to temp file — avoid /dev/stdin which doesn't work on Windows
TEMP_DIR=$(node -e "process.stdout.write(require('os').tmpdir())")
uip or folders list --all --output json > "${TEMP_DIR}/uip-folders.json"
```

Present the list to the user. Ask: "Which folder should this dashboard live in?"

> **Note:** `--all` bypasses the 50-item default cap. If the org has many folders, response may be slow — this is expected.

Once the user confirms a folder name:
```bash
FOLDER_KEY=$(node -e "
  const data = JSON.parse(require('fs').readFileSync(process.argv[1],'utf8'));
  const match = data.find(f => f.Name === '<FOLDER_NAME>');
  if (!match) { process.stderr.write('Folder not found\n'); process.exit(1); }
  process.stdout.write(match.Key);
" "${TEMP_DIR}/uip-folders.json")
rm -f "${TEMP_DIR}/uip-folders.json"
```

## Step 3 — Bump version

```bash
NEXT_SEMVER=$(node -e "
  const [major, minor, patch] = process.argv[1].split('.').map(Number);
  process.stdout.write([major, minor, patch + 1].join('.'));
" "$SEMVER")
```

**Version pre-check** — avoid a publish 409 by confirming this version doesn't exist yet:
```bash
TEMP_DIR=$(node -e "process.stdout.write(require('os').tmpdir())")
uip codedapp list --output json > "${TEMP_DIR}/uip-apps.json" 2>/dev/null
EXISTING=$(node -e "
  try {
    const d = JSON.parse(require('fs').readFileSync(process.argv[1],'utf8'));
    const pkg = d.find(p => p.Name === process.argv[2] && p.Version === process.argv[3]);
    process.stdout.write(pkg ? 'EXISTS' : 'OK');
  } catch { process.stdout.write('SKIP'); }
" "${TEMP_DIR}/uip-apps.json" "${ROUTING_NAME}" "${NEXT_SEMVER}")
rm -f "${TEMP_DIR}/uip-apps.json"
if [ "${EXISTING}" = "EXISTS" ]; then
  NEXT_SEMVER=$(node -e "const [a,b,c]=process.argv[1].split('.').map(Number); process.stdout.write([a,b,c+1].join('.'))" "$NEXT_SEMVER")
fi
```

## Step 4 — Show plan + confirm

Show the user:
```
Deploy plan:
  Dashboard:    <APP_NAME>
  Version:      <SEMVER> → <NEXT_SEMVER>
  Path name:    <ROUTING_NAME>
  Type:         Fresh deploy  OR  Upgrade (<SYSTEM_NAME>)
  Folder:       <folder name> (key: <FOLDER_KEY>)
```

Ask: **"Confirm deploy?"** — wait for `y` before proceeding.

## Step 5 — Production build (strip PAT)

Temporarily move `.env.local` so PAT doesn't enter the bundle.
Restore it regardless of build success or failure:

```bash
cd <PROJECT_DIR>
[ -f .env.local ] && mv .env.local .env.local.deploy-bak
npm run build
BUILD_EXIT=$?
# Restore unconditionally — runs on success AND failure
[ -f .env.local.deploy-bak ] && mv .env.local.deploy-bak .env.local
[ $BUILD_EXIT -ne 0 ] && echo "BUILD_FAILED" && exit 1
```

## Step 6 — Pack

`-n` here is the **routing slug** (package identifier, not display name):

```bash
uip codedapp pack dist \
  -n "${ROUTING_NAME}" \
  -v "${NEXT_SEMVER}" \
  --output json
```

## Step 7 — Publish (with transient-error retry)

`-n` here is the **routing slug** (same as pack):

```bash
TEMP_DIR=$(node -e "process.stdout.write(require('os').tmpdir())")

for ATTEMPT in 1 2 3 4; do
  uip codedapp publish \
    -n "${ROUTING_NAME}" \
    -v "${NEXT_SEMVER}" \
    --output json > "${TEMP_DIR}/uip-publish.json" 2>&1
  PUBLISH_EXIT=$?
  PUBLISH_OUT=$(cat "${TEMP_DIR}/uip-publish.json")

  # Success
  [ $PUBLISH_EXIT -eq 0 ] && break

  # 409 version conflict — increment version and retry
  if echo "${PUBLISH_OUT}" | grep -q "409\|already exists"; then
    NEXT_SEMVER=$(node -e "const [a,b,c]=process.argv[1].split('.').map(Number); process.stdout.write([a,b,c+1].join('.'))" "$NEXT_SEMVER")
    uip codedapp pack dist -n "${ROUTING_NAME}" -v "${NEXT_SEMVER}" --output json
    continue
  fi

  # Transient Cloudflare errors (520/522/524) or HTML response — wait and retry
  if echo "${PUBLISH_OUT}" | grep -qE "5[0-9]{2}|<!DOCTYPE|<html"; then
    WAIT=$((ATTEMPT * 5))
    sleep $WAIT
    continue
  fi

  # Non-retryable error
  echo "Publish failed: ${PUBLISH_OUT}" && exit 1
done
[ $PUBLISH_EXIT -ne 0 ] && echo "Publish failed after 4 attempts" && exit 1

# Extract deployVersion — process.argv avoids /dev/stdin issues on Windows
DEPLOY_VERSION=$(node -e "
  try {
    const d = JSON.parse(process.argv[1]);
    process.stdout.write(String(d.DeploymentVersion || d.deploymentVersion || ''));
  } catch { process.stdout.write(''); }
" "$PUBLISH_OUT")
rm -f "${TEMP_DIR}/uip-publish.json"
```

## Step 8 — Deploy

> **Flag name:** `--path-name` (NOT `--routing-name` — that flag does not exist).
> `-n` here is the **sanitized display name** matching the published package slug.

```bash
uip codedapp deploy \
  -n "${APP_SAFE_NAME}" \
  --path-name "${ROUTING_NAME}" \
  --folder-key "${FOLDER_KEY}" \
  --output json > "${TEMP_DIR}/uip-deploy.json" 2>&1
DEPLOY_EXIT=$?
DEPLOY_OUT=$(cat "${TEMP_DIR}/uip-deploy.json")

# Path-name collision — regenerate suffix and retry (up to 3 times)
COLLISION_ATTEMPTS=0
while echo "${DEPLOY_OUT}" | grep -qiE "conflict|already.*exist|path.*name" && [ $COLLISION_ATTEMPTS -lt 3 ]; do
  COLLISION_ATTEMPTS=$((COLLISION_ATTEMPTS+1))
  NEW_SUFFIX=$(node -e "process.stdout.write(Math.random().toString(36).slice(2,6))")
  NEW_ROUTING=$(echo "${ROUTING_NAME}" | sed "s/-[a-z0-9]*$/-${NEW_SUFFIX}/")
  # Update routing name and re-pack + re-publish + re-deploy with new slug
  uip codedapp pack dist -n "${NEW_ROUTING}" -v "${NEXT_SEMVER}" --output json
  uip codedapp publish -n "${NEW_ROUTING}" -v "${NEXT_SEMVER}" --output json
  uip codedapp deploy \
    -n "${APP_SAFE_NAME}" \
    --path-name "${NEW_ROUTING}" \
    --folder-key "${FOLDER_KEY}" \
    --output json > "${TEMP_DIR}/uip-deploy.json" 2>&1
  DEPLOY_EXIT=$?
  DEPLOY_OUT=$(cat "${TEMP_DIR}/uip-deploy.json")
  [ $DEPLOY_EXIT -eq 0 ] && ROUTING_NAME="${NEW_ROUTING}" && break
done

[ $DEPLOY_EXIT -ne 0 ] && echo "Deploy failed: ${DEPLOY_OUT}" && exit 1

# Parse response — process.argv avoids /dev/stdin issues on Windows
SYSTEM_NAME_NEW=$(node -e "
  try {
    const d = JSON.parse(process.argv[1]);
    process.stdout.write(d.SystemName || d.systemName || '');
  } catch { process.stdout.write(''); }
" "$DEPLOY_OUT")
APP_URL=$(node -e "
  try {
    const d = JSON.parse(process.argv[1]);
    process.stdout.write(d.AppUrl || d.appUrl || '');
  } catch { process.stdout.write(''); }
" "$DEPLOY_OUT")
rm -f "${TEMP_DIR}/uip-deploy.json"
```

## Step 9 — Update state.json

```bash
node -e "
  const fs = require('fs'), path = require('path');
  const fp = path.join('.dashboard', 'state.json');
  const state = JSON.parse(fs.readFileSync(fp, 'utf8'));
  state.app.semver = process.argv[1];
  state.app.routingName = process.argv[2];
  state.deployment.folderKey = process.argv[3];
  state.deployment.systemName = process.argv[4] || state.deployment.systemName;
  state.deployment.deployVersion = process.argv[5] || state.deployment.deployVersion;
  state.deployment.appUrl = process.argv[6] || state.deployment.appUrl;
  state.deployment.lastDeployedAt = new Date().toISOString();
  const tmp = fp + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(state, null, 2));
  fs.renameSync(tmp, fp);
  process.stdout.write('✓ state updated\n');
" "$NEXT_SEMVER" "$ROUTING_NAME" "$FOLDER_KEY" "$SYSTEM_NAME_NEW" "$DEPLOY_VERSION" "$APP_URL"
```

## Step 10 — Report

```
✅ Your **<APP_NAME>** is live.

<APP_URL>

Version <NEXT_SEMVER> deployed to <folder name>.
To update it later, say "deploy this dashboard" again.
```

## Error handling

| Error | Action |
|---|---|
| `npm run build` fails | Fix build errors first (see `../../debug.md`); PAT is restored automatically |
| `uip codedapp pack` fails | Verify `dist/` exists; run `npm run build` first |
| Publish 409 (version conflict) | Auto-increments version and retries (handled in Step 7 loop) |
| Publish 5xx / HTML response | Retry with exponential backoff (handled in Step 7 loop) |
| Deploy `--path-name` conflict | Auto-regenerates suffix and retries (handled in Step 8 loop) |
| Deploy folder error | Re-run `uip or folders list --all` and verify the key |
| Deploy "not published yet" | Likely name mismatch — verify `APP_SAFE_NAME` matches the routing slug |
| state.json corrupt | Show raw error; user must run build again to regenerate |

## Dashboard-specific rules

- App type is always **Web** — never pass `-t Action`
- Routing name is permanent after first successful deploy — never change it manually
- PAT must NOT be in production bundle — `failBuildIfPatSet` Vite plugin enforces this
- `deployVersion` in state.json is the Orchestrator integer version (separate from semver) — required for upgrade path
- **`--path-name`** is the correct flag for deploy (not `--routing-name` which does not exist)
- Always sanitize display names before passing to `-n` in deploy — the CLI strips special chars and may produce a slug that doesn't match your published package
