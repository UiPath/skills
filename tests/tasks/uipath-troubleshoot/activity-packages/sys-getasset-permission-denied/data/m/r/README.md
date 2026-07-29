# Get Asset Failure — Permission Denied

This scenario reproduces a runtime `Get Credential` failure caused by
the **robot account lacking `Assets.View` permission** on the target
folder. Orchestrator returns HTTP **403** / error code **0** with the
message "You are not authorized! The robot account does not have the
required permissions on Assets in this folder."

## What this scenario uncovers

**Root Cause:** The `Get Credential` activity in `Main.xaml` references
a correctly-spelled asset (`myHiddenAsset`) in a real folder (`Remote
Debugging`). Both the asset and the folder exist and are visible to
the CLI user — but the robot account that runs the job lacks the
`Assets.View` permission on the folder, so Orchestrator returns 403.

This maps to:
`references/activity-packages/system-activities/playbooks/get-asset-permission-denied.md`
(the "Robot account role does not include View permission on Assets"
branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | synthesized UiPath project — same scaffold as `getasset-name-mismatch` with the typo fixed and the FolderPath set to a real folder |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

> **Note on fixtures.** Like sibling scenarios, fixtures here were
> authored from the documented playbook signature rather than captured
> from a real `.local/investigations/` session. Regenerate via
> `_shared/scripts/generate_scenario.py` from a real failed-job
> session before treating this test's score as a regression signal.

## How this differs from sibling scenarios

| Dimension | `name-mismatch` | `folder-scope-mismatch` | `permission-denied` (this) |
|---|---|---|---|
| AssetName | typo (`myHiddenAset`) | correct (`myHiddenAsset`) | correct (`myHiddenAsset`) |
| FolderPath | real folder | non-existent (`OldDevFolder`) | real (`Remote Debugging`) |
| Asset visible in folder asset list? | no (different name) | n/a (folder doesn't exist) | **yes** |
| Folder visible in folder list? | yes | **no** | yes |
| HTTP status / error code | 404 / 1002 | 403 / 1100 | **403 / 0** |
| Error message anchor | "Could not find the asset" | "Folder ... does not exist or the user does not have access" | "You are not authorized" / "required permissions on Assets" |
| Matched playbook | `get-asset-not-found.md` | `get-asset-folder-scope-mismatch.md` | `get-asset-permission-denied.md` |

The asset list and folder list fixtures here both return the expected
positive content (asset is present, folder is present). The agent must
notice that what's failing is **authorization**, not **discovery**.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook AND reached the same root cause as `RESOLUTION.md`
- Conclusion must explicitly name the missing `Assets.View` permission (or equivalent role-level fix) on the robot account; must NOT reach the wrong conclusion as asset-not-found or folder-not-found

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name getasset-permission-denied --apply
```
