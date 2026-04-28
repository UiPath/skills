# deploy-cli

## Purpose
Happy-path deploy via the `uip codedapp` CLI chain. First-choice engine; `deploy-fallback.md` takes over only on rare CLI bugs (currently the hardcoded-`versions/1` path on some upgrade paths).

## Inputs
- state.json with Build fields filled.
- User-confirmed deploy plan.

## Outputs
Updated `state.json.deployment.*`; live app URL.

## Rules
1. **`--output json` on every `uip codedapp` call** — parse `Data` / `Message`.
2. **`-n` semantics differ between pack/publish and deploy.**
   - On `pack` and `publish`: `-n` is the **package name** — pass the routing slug (`govdash-...`) so the nupkg filename and registered package match.
   - On `deploy`: `-n` is the **App name** — pass the user-friendly display title (`Agent Health Dashboard`). The slug goes in via `--routing-name`. The catalog title in the Governance Unified Portal comes from this `-n` value.
3. **`--type Action` on publish.** The platform recognizes the package as an action subtype from this flag plus the action-schema in CWD (project root) and `dist/`.
4. **`--routing-name` on deploy.** Pass it explicitly (alongside `-n`) for clarity even though it currently equals `-n`.
5. **`--description "PINNED"` only with explicit user opt-in.** No default — the deploy plan/confirm gate asks the user explicitly when their prompt was silent on pinning. Pass `--description "PINNED"` when the user said yes; omit the flag entirely (don't pass `--description ""`) when the user said no. See [../plugins/deploy/impl.md § Pin-on-deploy detection](../plugins/deploy/impl.md) for the prompt-scan + ASK flow.
6. **`action-schema.json` lives at the project root for `uip codedapp publish`** AND in `public/` for Vite to copy into `dist/`. The publisher reads from CWD; the runtime reads from the bundled location. The scaffold ships both; never drop the project-root copy.
7. **Halt on non-zero exit** unless the error signature matches a known auto-recoverable case (§ Auto-recovery signatures).
8. **Wrap publish + deploy in the transient-error retry loop** (`uip` CLI does NOT retry 5xx itself). See [../plugins/deploy/impl.md § Transient-error retry loop](../plugins/deploy/impl.md).
9. **Detect Cloudflare HTML responses** — even with `--output json`, gateway errors (520/522/524) come back as HTML. Collapse to a single-line "Upstream gateway error — retrying" message.
10. **Routing-name collision triggers regenerate-and-retry** (3 attempts max), then halt. See [../plugins/deploy/impl.md § Routing-name retry](../plugins/deploy/impl.md).
11. **`deploymentId` may be null after a fresh deploy** — the CLI doesn't currently surface it. Leave the field null; it backfills on first upgrade via `discover-deployment.sh`. Do NOT halt because of this.
12. **Construct the deployed-app URL from state, not from CLI output.** The CLI doesn't print a URL on successful deploy. Compute as `https://${orgName}.${envInfix}uipath.host/${routingName}` — that's the only confirmed-working pattern.
13. **Detect "version exists" before publish to avoid wasted slots.** Failed publish (e.g., schema validation) still occupies the semver. Before publish, list existing versions for the routing-name; if current `state.app.semver` is taken, suggest a bump in the plan re-prompt rather than letting the publish fail.
14. **Bump `state.app.semver` on successful deploy.** After the deploy succeeds, write the next patch version (`1.0.2` → `1.0.3`) to state.json so the next "deploy this" starts at a fresh number. Skip the bump on failure.

## Pipeline

### 1. `npm run build`
```bash
cd <project>
npm run build
```
Verify `<project>/dist/` exists, contains `index.html` AND `action-schema.json` (the latter copied from `public/` by Vite).

### 2. Pack
```bash
uip codedapp pack dist -n <state.app.routingName> -v <state.app.semver> --output json
```
Any "invalid name" warning means the routing name doesn't satisfy server constraints (lowercase alphanumeric + hyphens) — regenerate via intent-capture's recipe.

### 3. Publish (wrapped in transient-error retry loop)
```bash
RESP=$(attempt 'uip codedapp publish --type Action -n "$ROUTING_NAME" -v "$SEMVER" --output json')
DEPLOY_VERSION=$(echo "$RESP" | jq -r '.Data.DeployVersion')
```
Save `DEPLOY_VERSION` as `state.deployment.deployVersion`.

### 4. Deploy (wrapped in transient-error retry loop AND routing-name retry)
```bash
# -n carries the user-friendly App name (e.g., "Agent Health Dashboard");
# --routing-name carries the slug (e.g., "govdash-agent-health-x7k2").
# --description "PINNED" only on explicit user opt-in.
DEPLOY_CMD="uip codedapp deploy -n \"$APP_NAME\" --routing-name \"$ROUTING_NAME\" --folder-key \"$FOLDER_KEY\""
[[ "$PIN" == "yes" ]] && DEPLOY_CMD+=' --description "PINNED"'
DEPLOY_CMD+=' --output json'
RESP=$(attempt "$DEPLOY_CMD")
```

**Flag discipline:**
- `-n` = App name (user-friendly display title, e.g., `Agent Health Dashboard`).
- `--routing-name` = URL slug (e.g., `govdash-agent-health-dash-x7k2`).
- `--description "PINNED"` = pin signal (default). Omit the flag entirely on opt-out — never pass `--description ""`.
- `--folder-key` required (otherwise interactive picker hangs).
- **Do NOT pass `-v <semver>`.** The `-v` flag expects a `deployVersion` integer; passing semver right after a successful publish errors with `App has not been published yet`. Omit `-v` and the CLI deploys the latest published version.

Parse:
- Success → `{Data.SystemName, Data.AppUrl, ...}`. `Data.DeploymentId` may not be present in current CLI output — leave that field null.
- Stderr contains `routingName already exists` / `Routing name is already taken` → **routing-name collision**: regenerate suffix, re-pack, re-publish, re-deploy (max 3 attempts).
- Stderr contains `app already deployed in folder` (1004) → **auto-reconcile** via `assets/scripts/discover-deployment.sh` → switch to upgrade.
- Stderr contains `User force closed the prompt` → `--folder-key` wasn't passed (or was empty); recheck and retry.
- Stderr contains `App has not been published yet` despite a successful publish → `-v` was passed with a semver; drop the flag and retry.

## Auto-recovery signatures

| Stderr / response contains | Action |
|---|---|
| `<!DOCTYPE html>` / `Bad gateway` / `Web server is down` | Transient 5xx; retry per transient-error loop (5s, 10s, 20s; 4 attempts). |
| `routingName already exists` / `Routing name is already taken` | Regenerate routing-name suffix, re-pack, re-publish, re-deploy (max 3 attempts). |
| `app already deployed in folder` (1004) | Run `discover-deployment.sh`; populate `state.deployment.*`; retry as upgrade via CLI. |
| `User force closed the prompt` | `--folder-key` missing; add the flag and retry (no fallback needed). |
| `App has not been published yet` (right after a successful publish) | `-v <semver>` passed; drop the flag and retry. |

## State updates
After successful deploy, atomic write per [state-file.md](state-file.md). The CLI does NOT print an app URL — construct it deterministically. Bump semver to the next patch.

```bash
APP_URL="https://${ORG_NAME}.${ENV_INFIX}uipath.host/${ROUTING_NAME}"
NEXT_SEMVER=$(node -e "
  const v = '${SEMVER}'.split('.').map(Number);
  v[2]++;
  console.log(v.join('.'));
")
```

```json
{
  "app": {
    "routingName": "<final routing name — may differ from initial if retried>",
    "semver": "<NEXT_SEMVER — bumped patch>"
  },
  "deployment": {
    "systemName": "<from CLI Data.SystemName>",
    "deploymentId": null,
    "deployVersion": <from publish step>,
    "appUrl": "<constructed from orgName + envInfix + routingName>",
    "deployedAt": "<ISO now>",
    "lastPublishAt": "<ISO of publish step>"
  }
}
```

## Error paths
| Condition | Action |
|---|---|
| `dist/` missing after `npm run build` | Halt. |
| `dist/action-schema.json` missing | Halt; verify `public/action-schema.json` is in the project. |
| `uip` not on PATH | Halt; instruct install. |
| Pack: `invalid name` | Halt; agent regenerates routingName. |
| Publish: `version already exists` | Halt; suggest bump; never silent-bump. |
| Transient 5xx exhausted (4 attempts) | Halt with the friendly "Upstream gateway error — try again in a few minutes" message. |
| Routing-name retries exhausted (3 attempts) | Halt; instruct user to override `app.routingName` manually in state.json. |
