# deploy-fallback

## Purpose
Direct-API deploy when the `uip codedapp deploy` CLI fails for reasons that aren't covered by the auto-recovery signatures in [deploy-cli.md](deploy-cli.md). Triggered narrowly — never eagerly. Insurance against rare CLI bugs (e.g., the hardcoded-`versions/1/deploy` path that some CLI builds emit on upgrade flows).

## Inputs
- state.json (populated through publish step).
- deployVersion from publish.
- Access token from `~/.uipath/.auth.json`.

## Outputs
Deployment created via direct HTTP; `state.deployment.*` populated.

## Rules
1. **Triggered narrowly.** Only when `uip codedapp deploy` returns an error that isn't auto-recoverable per `deploy-cli.md` AND a direct-API equivalent is known to work. Routine 5xx and routing-name collisions are handled by the CLI loops, not here.
2. **Uses `assets/scripts/deploy-direct-api.sh`** — cross-platform bash, all headers + URL shape encoded in the script.
3. **Fresh vs upgrade inferred from `state.deployment.systemName`** per `state-file.md` ownership rules.
4. **Auto-reconcile on `1004 already deployed`** — when a fresh POST hits this, run `discover-deployment.sh`, populate systemName/deploymentId, retry as PATCH.

## Deploy endpoints

Base: `https://<env>.uipath.com/<orgId>/apps_/default/api/v1/default/models`

| Operation | Method + Path | Body |
|---|---|---|
| Fresh deploy | `POST /<systemName>/publish/versions/<deployVersion>/deploy` | `{title: <state.app.name>, routingName: <state.app.routingName>}` |
| Upgrade | `PATCH /deployed/apps/<deploymentId>` | `{title: <state.app.name>, version: <deployVersion>}` |
| List published versions | `GET /<systemName>/publish/versions` | — |
| List deployed apps in folder | `GET /deployed/apps` | — |

`title` is the user-friendly display name (`state.app.name`); `routingName` is the URL slug (`state.app.routingName`).

### Required headers (all endpoints)
```
Authorization: Bearer <access_token from .uipath/.auth.json>
x-uipath-internal-tenantid: <tenantId>
x-uipath-folderkey: <state.folderKey>
Content-Type: application/json   (on writes)
```

Append these query params (CLI does; some endpoints 400 without them):
```
?x-uipath-tenantname=<tenantName>&x-uipath-orgname=<orgName>
```

## Pipeline
```bash
bash assets/scripts/deploy-direct-api.sh \
  --env <env> \
  --org <orgName> \
  --org-id <orgId> \
  --tenant <tenantName> \
  --tenant-id <tenantId> \
  --folder <folderKey> \
  --system <state.deployment.systemName or "" for fresh> \
  --deployment <state.deployment.deploymentId or "" for fresh> \
  --version <deployVersion> \
  --title "<state.app.name>" \
  --routing <state.app.routingName>
```

Script returns JSON with `systemName`, `deploymentId`, `appUrl` — parse, update state.

## Reconciliation on `1004`
```bash
bash assets/scripts/discover-deployment.sh \
  --env <env> --org-id <orgId> --tenant-id <tenantId> --folder <folderKey> \
  --search <state.app.routingName>
```
Returns `systemName`, `deploymentId`, current `semVersion`, `deployVersion`. Populate state; retry as PATCH.

## Error paths
| Condition | Action |
|---|---|
| Direct-API returns 401 | Re-read token from `.uipath/.auth.json`; if still 401, halt + instruct `uip login`. |
| Direct-API returns 403 | Token lacks scope; halt + diagnose. |
| Direct-API returns 5xx / Cloudflare HTML | Same retry discipline as the CLI loop (5s, 10s, 20s; 4 attempts). |
| Script can't find `jq` | Require `jq` install OR use node equivalent. |
