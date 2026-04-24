# deploy-fallback

## Purpose
Direct-API deploy when `uip codedapp deploy` hits the hardcoded-`versions/1/deploy` bug. Triggered ONLY on `clientId not found` stderr signature — never eagerly.

## Inputs
- state.json (populated through publish step).
- deployVersion from publish.
- Access token from `.uipath/.auth.json`.

## Outputs
Deployment created via direct HTTP; `state.deployment.*` populated.

## Rules
1. **Triggered only on exact stderr match** — never eagerly. Users shouldn't see this path unless the CLI bug fires.
2. **Uses `assets/scripts/deploy-direct-api.sh`** — cross-platform bash, all headers + URL shape encoded in the script.
3. **Fresh vs upgrade inferred from `state.deployment.systemName`** per `state-file.md` ownership rules.
4. **Auto-reconcile on `1004 already deployed`** — when a fresh POST hits this, run `discover-deployment.sh`, populate systemName/deploymentId, retry as PATCH.

## Deploy endpoints

Base: `https://<env>.uipath.com/<orgId>/apps_/default/api/v1/default/models`

| Operation | Method + Path | Body |
|---|---|---|
| Fresh deploy | `POST /<systemName>/publish/versions/<deployVersion>/deploy` | `{title: <lowercase-routingName>, routingName: <lowercase-routingName>}` |
| Upgrade | `PATCH /deployed/apps/<deploymentId>` | `{title: <app.name>, version: <deployVersion>}` |
| List published versions | `GET /<systemName>/publish/versions` | — |
| List deployed apps in folder | `GET /deployed/apps` | — |

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
  --title <app.name> \
  --routing <app.routingName>
```

Script returns JSON with `systemName`, `deploymentId`, `appUrl` — parse, update state.

## Reconciliation on `1004`
```bash
bash assets/scripts/discover-deployment.sh \
  --env <env> --org-id <orgId> --tenant-id <tenantId> --folder <folderKey> \
  --search <app.name>
```
Returns `systemName`, `deploymentId`, current `semVersion`, `deployVersion`. Populate state; retry as PATCH.

## Error paths
| Condition | Action |
|---|---|
| Direct-API returns 401 | Re-read token from `.uipath/.auth.json`; if still 401, halt + instruct `uip login`. |
| Direct-API returns 403 | Token lacks scope; unusual in full-session-token mode. Halt + diagnose. |
| Script can't find `jq` | Require `jq` install OR use node equivalent. |
| CLI bug fixed in current version (no `clientId not found`) | Fallback never triggers; script stays as insurance. |
