# Get Asset Failure — Robot Not Authenticated / Unlicensed

This scenario reproduces a runtime `Get Credential` failure caused by
the **robot account being unlicensed** (Connected, Unlicensed in
Orchestrator). Orchestrator returns HTTP **401** / "You are not
authenticated! Error code: 0" — the failure is at the
authentication/licensing layer, before any asset call can execute.

## What this scenario uncovers

**Root Cause:** The Get Credential activity in `Main.xaml` targets a
correctly-named Credential asset (`myHiddenAsset`) in a real folder
(`Remote Debugging`). All the asset-level configuration is correct.
The failure is at the robot identity layer: the robot account
(`RobotUser1`) is shown in Orchestrator as `IsLicensed: false`,
`LicenseType: null` — i.e., Connected but Unlicensed.

This maps to:
`references/activity-packages/system-activities/playbooks/get-asset-robot-not-authenticated.md`
(medium-confidence playbook).

> **Why "medium-confidence":** the same error code (0) and HTTP path
> (4xx) can arise from several distinct causes per the playbook —
> robot unlicensed, machine key mismatch, package regression in
> `UiPath.System.Activities` 20.10.1+, interactive sign-in disabled.
> This scenario reproduces the most common branch (unlicensed
> robot). The agent must inspect license state to distinguish.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project — Get Credential activity, correctly configured at every asset layer |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The smoking gun is the combination of:

1. The error message phrasing — "not **authenticated**" (distinct from
   permission-denied's "not **authorized**").
2. `or users list` output showing the robot account `RobotUser1` with
   `IsLicensed: false`, `LicenseType: null`.

## How this differs from sibling scenarios

| Dimension | `name-mismatch` | `folder-scope-mismatch` | `permission-denied` | `wrong-activity-type` | `per-robot-no-value` | `robot-not-authenticated` (this) |
|---|---|---|---|---|---|---|
| AssetName | typo | correct | correct | correct | correct | correct |
| FolderPath | real | non-existent | real | real | real | real |
| Asset visible in folder asset list? | no | n/a | yes | yes (wrong type) | yes (right type) | yes |
| Permission issue? | n/a | n/a | yes (`Assets.View` missing) | n/a | n/a | no (robot has Assets.View) |
| Robot license? | n/a | n/a | n/a | n/a | n/a | **none — unlicensed** |
| Error phrasing | "Could not find the asset" | "Folder ... does not exist" | "not **authorized**" | "Invalid asset type" | "does not have a value associated with this robot" | **"not authenticated"** |
| HTTP / error code | 404 / 1002 | 403 / 1100 | 403 / 0 | 400 | n/a | **401 / 0** |
| Matched playbook | `get-asset-not-found.md` | `get-asset-folder-scope-mismatch.md` | `get-asset-permission-denied.md` | `get-asset-wrong-activity-type.md` | `get-asset-per-robot-no-value.md` | `get-asset-robot-not-authenticated.md` |

The agent must distinguish "not authenticated" (401, this scenario)
from "not authorized" (403, `permission-denied`) — same error code (0)
but different word, different cause, different fix.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook AND reached the same root cause as `RESOLUTION.md`
- Conclusion must (a) name the robot account `RobotUser1`, (b) recognize that it is unlicensed, and (c) recommend assigning a license

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name getasset-robot-not-authenticated --apply
```
