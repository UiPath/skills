# deploy-cli

## Purpose
Happy-path deploy via the `uip codedapp` CLI chain. First-choice engine; `deploy-fallback.md` takes over when the CLI hits the hardcoded-`versions/1` bug.

## Inputs
- state.json with Build fields filled.
- User-confirmed deploy plan.

## Outputs
Updated `state.json.deployment.*`; live app URL.

## Rules
1. **`--output json` on every `uip codedapp` call** — parse `Data` / `Message`.
2. **Halt on non-zero exit** unless the error signature matches a known auto-recoverable case (§ Auto-fallback signatures).
3. **nupkg case discipline** — pack force-lowercases; rename before publish if needed.
4. **Record `deployVersion` immediately after publish** — the server-side integer is what deploy needs.

## Pipeline

### 1. `npm run build`
```bash
cd <project>
npm run build
```
Verify `<project>/dist/` exists + has `index.html`.

### 2. Pack
```bash
uip codedapp pack dist -n <state.app.name> -v <state.app.semver> --output json
```
If output contains `"⚠️ App name ... contains invalid characters. Using sanitized name:"`, the nupkg was written lowercased. Rename:
```bash
mv .uipath/<lower>.<ver>.nupkg .uipath/<state.app.name>.<ver>.nupkg
```

### 3. Publish
```bash
uip codedapp publish -n <state.app.name> -v <state.app.semver> --output json
```
Parse `Data.DeployVersion` → save as `state.deployment.deployVersion`.

### 4. Deploy
```bash
uip codedapp deploy -n <state.app.name> --folder-key <state.folderKey> --output json
```

**Critical CLI flag discipline (learned the hard way):**

- `--folder-key` is **required** in non-interactive mode. Without it the CLI opens an interactive folder picker; agents running non-interactively hang then fail with `User force closed the prompt`. Always pass the flag — `state.folderKey` was resolved in [../plugins/deploy/impl.md § Step 2b](../plugins/deploy/impl.md).
- **Do NOT pass `-v <semver>`** on deploy. The `-v` flag expects a `deployVersion` integer (from publish output), NOT the semver. Passing `-v 1.0.0` right after publishing 1.0.0 still errors with `App has not been published yet`. Omit `-v` — the CLI deploys the latest published version, which is what we want. Only pass `-v` if you're intentionally pinning to a specific `Data.DeployVersion` integer.
- `-n <app.name>` matches the publish's `-n`. If pack force-lowercased the nupkg filename and we renamed it back to PascalCase, pass that same PascalCase here.

Parse:
- Success → `{systemName, deploymentId, appUrl, ...}`.
- Stderr contains `clientId not found` → **auto-hand off to [deploy-fallback.md](deploy-fallback.md)**.
- Stderr contains `app already deployed in folder` → **auto-reconcile** via `assets/scripts/discover-deployment.sh` → switch to upgrade.
- Stderr contains `User force closed the prompt` → `--folder-key` wasn't passed (or was passed as empty). Re-check `state.folderKey`, retry.
- Stderr contains `App has not been published yet` despite a publish step that succeeded → `-v` was passed with a semver. Drop the `-v`; retry.

## Auto-fallback signatures

| Stderr contains | Action |
|---|---|
| `clientId not found` | Use deploy-fallback (direct-API with correct deployVersion) |
| `app already deployed in folder` | Use discover-deployment.sh; populate state.deployment.*; retry as upgrade via CLI |
| `User force closed the prompt` | `--folder-key` missing; add the flag and retry (no fallback needed) |
| `App has not been published yet` (right after a successful publish) | `-v <semver>` passed; drop the flag and retry |

## State updates
After successful deploy:
```json
{
  "deployment": {
    "systemName": "<from CLI result>",
    "deploymentId": "<from CLI result>",
    "deployVersion": <from publish step>,
    "appUrl": "<from CLI result>",
    "deployedAt": "<ISO now>",
    "lastPublishAt": "<ISO of publish step>"
  }
}
```

Atomic write via [state-file.md](state-file.md).

## Error paths
| Condition | Action |
|---|---|
| `dist/` missing after `npm run build` | Halt. |
| `uip` not on PATH | Halt; instruct install. |
| Pack: `invalid name` | Halt; suggest cleaner name. |
| Publish: `version already exists` | Halt; suggest bump; never silent-bump. |
| CLI 5xx | Retry 3× exponential (1s, 3s, 9s). |
| Deploy: `Name can only contain lowercase alphanumeric + hyphens` | Halt; user picks new routing; update state.json. |
