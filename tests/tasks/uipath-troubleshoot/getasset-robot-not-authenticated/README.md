# Get Asset Failure — Robot Not Authenticated (API-Token Layer)

This scenario reproduces a runtime `Get Credential` failure where the
robot is **licensed, connected, and correctly permissioned**, the asset
and folder are correctly configured — yet the activity's Orchestrator
REST call is rejected with HTTP **401** / "You are not authenticated!
Error code: 0". The failure is at the robot **identity / API-token**
layer, surfaced *after* the job has already started running.

## What this scenario uncovers

**Root Cause:** The Get Credential activity in `Main.xaml` targets a
correctly-named Credential asset (`myHiddenAsset`) in a real folder
(`Remote Debugging`). All asset-level configuration is correct, the
robot account (`RobotUser1`) holds the right roles, and it is licensed
and connected (`IsLicensed: true`, `LicenseType: Unattended`). The job
**started and ran ~1 second** before faulting *inside* `Main.xaml` at
`GetRobotCredential` — which proves the robot acquired a runtime, so
licensing is not the problem. The robot's Orchestrator API token is
being rejected when the activity calls the REST API.

This maps to:
`references/activity-packages/system-activities/playbooks/get-asset-robot-not-authenticated.md`
(medium-confidence playbook).

> **Why "medium-confidence":** the same 401 / "not authenticated"
> signature on a *running* job can arise from several robot-identity
> causes per the playbook — machine-key / client-credential mismatch,
> robot-key authentication disabled in tenant security, or a
> `UiPath.System.Activities` auth regression. The available evidence
> (everything else correct) does not single one out, so the resolution
> is a ranked checklist. The agent must localize the fault to the
> authentication / token layer and rule out the licensing red herring.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project — Get Credential activity, correctly configured at every asset layer |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The smoking gun is the combination of:

1. The error message phrasing — "not **authenticated**" / HTTP 401
   (distinct from permission-denied's "not **authorized**" / 403).
2. The job has a `StartTime` and ran ~1s before faulting at the
   activity — it **executed**, so the robot is licensed enough to run.
3. `or users list` shows `RobotUser1` licensed and connected
   (`IsLicensed: true`, `LicenseType: Unattended`,
   `ConnectionState: Connected`), and asset / folder / type /
   permissions all check out — leaving the robot's API-token
   authentication as the only failing layer.

## How this differs from sibling scenarios

| Dimension | `name-mismatch` | `folder-scope-mismatch` | `permission-denied` | `wrong-activity-type` | `per-robot-no-value` | `robot-not-authenticated` (this) |
|---|---|---|---|---|---|---|
| AssetName | typo | correct | correct | correct | correct | correct |
| FolderPath | real | non-existent | real | real | real | real |
| Asset visible in folder asset list? | no | n/a | yes | yes (wrong type) | yes (right type) | yes |
| Permission issue? | n/a | n/a | yes (`Assets.View` missing) | n/a | n/a | no (robot has Assets.View) |
| Robot licensed & connected? | n/a | n/a | n/a | n/a | n/a | **yes — licensed, connected** |
| Did the job start/run? | n/a | n/a | n/a | n/a | n/a | **yes — ran ~1s, faulted at the activity** |
| Error phrasing | "Could not find the asset" | "Folder ... does not exist" | "not **authorized**" | "Invalid asset type" | "does not have a value associated with this robot" | **"not authenticated"** |
| HTTP / error code | 404 / 1002 | 403 / 1100 | 403 / 0 | 400 | n/a | **401 / 0** |
| Matched playbook | `get-asset-not-found.md` | `get-asset-folder-scope-mismatch.md` | `get-asset-permission-denied.md` | `get-asset-wrong-activity-type.md` | `get-asset-per-robot-no-value.md` | `get-asset-robot-not-authenticated.md` |

The agent must distinguish "not authenticated" (401, this scenario)
from "not authorized" (403, `permission-denied`) — same error code (0)
but different word, different cause, different fix — AND avoid the
licensing red herring: an unlicensed robot would never have started the
job, so a *running* job that 401s is an authentication/token failure,
not a licensing gap.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook AND reached the same root cause as `RESOLUTION.md`
- Conclusion must (a) name the robot account `RobotUser1`, (b) localize the failure to the robot authentication / API-token layer (explicitly NOT licensing, explicitly NOT permission), and (c) recommend at least one of: reconnect with the correct machine key, enable robot-key authentication, or check `UiPath.System.Activities` for the auth regression

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name getasset-robot-not-authenticated --apply
```
