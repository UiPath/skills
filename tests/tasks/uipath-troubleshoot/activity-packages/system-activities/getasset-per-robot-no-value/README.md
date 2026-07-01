# Get Asset Failure — Per-Robot Asset Has No Value

This scenario reproduces a runtime `Get Asset` failure caused by a
**per-robot asset configured without a value entry for the executing
robot**. Orchestrator returns "The asset 'MyPerRobotConfig' does not
have a value associated with this robot."

## What this scenario uncovers

**Root Cause:** The `Get Asset` activity in `Main.xaml` targets a
correctly-named asset in a real folder, and the asset's `ValueType` is
compatible with the activity. But the asset is configured with
`ValueScope: "PerRobot"` and the robot running the job has no entry in
the per-robot value table. Orchestrator therefore reports the asset
has no value for this robot.

This maps to:
`references/activity-packages/system-activities/playbooks/get-asset-per-robot-no-value.md`
(the "Asset uses 'Per Robot' value mode but no entry exists for the
executing robot" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | synthesized UiPath project — uses `Get Asset` (`GetRobotAsset`) rather than `Get Credential` to match the playbook's coverage |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

> **Note on fixtures.** Like sibling scenarios, fixtures here were
> authored from the documented playbook signature rather than captured
> from a real `.local/investigations/` session. Regenerate via
> `_shared/scripts/generate_scenario.py` from a real failed-job
> session before treating this test's score as a regression signal.

## How this differs from sibling scenarios

| Dimension | `name-mismatch` | `folder-scope-mismatch` | `permission-denied` | `wrong-activity-type` | `per-robot-no-value` (this) |
|---|---|---|---|---|---|
| Activity | Get Credential | Get Credential | Get Credential | Get Credential | **Get Asset** |
| `AssetName` | typo | correct | correct | correct | correct |
| `FolderPath` | real folder | non-existent | real | real | real |
| Asset visible in folder asset list? | no | n/a | yes | yes (but wrong type) | yes (right type) |
| `ValueScope` | n/a | n/a | n/a | n/a | **PerRobot** |
| Per-robot value entry for executing robot? | n/a | n/a | n/a | n/a | **no** |
| HTTP / error signature | 404 / 1002, "Could not find the asset" | 403 / 1100, "Folder ... does not exist" | 403 / 0, "You are not authorized" | 400, "Invalid asset type" | **"does not have a value associated with this robot"** |
| Matched playbook | `get-asset-not-found.md` | `get-asset-folder-scope-mismatch.md` | `get-asset-permission-denied.md` | `get-asset-wrong-activity-type.md` | `get-asset-per-robot-no-value.md` |

This scenario forces the agent past four rule-outs (asset exists, folder
exists, permission is fine, type matches) before landing on the
per-robot configuration. The asset list fixture is the decisive signal:
it shows `MyPerRobotConfig` with `ValueScope: "PerRobot"`, which together
with the error message points unambiguously at the per-robot value gap.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook AND reached the same root cause as `RESOLUTION.md`
- Conclusion must name the per-robot scope and recommend either adding a per-robot value entry OR switching the asset's scope to Global

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name getasset-per-robot-no-value --apply
```
