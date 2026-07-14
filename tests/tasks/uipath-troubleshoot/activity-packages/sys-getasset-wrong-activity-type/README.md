# Get Asset Failure — Wrong Activity for Asset Type

This scenario reproduces a runtime `Get Credential` failure caused by
an **activity-vs-asset-type mismatch**: the workflow uses the
`Get Credential` activity (`GetRobotCredential`), which only works on
assets of type `Credential`, but the asset it targets is actually
type `Text`. Orchestrator returns HTTP **400** with the error
"Activity does not work with assets of type 'Text'. Invalid asset type."

## What this scenario uncovers

**Root Cause:** The `Get Credential` activity in `Main.xaml` targets
`AssetName="ApiBaseUrl"` in the `Remote Debugging` folder. The asset
exists in that folder but its `ValueType` is `Text`, not `Credential`.
The runtime mismatch is rejected before the credential read can
proceed.

This maps to:
`references/activity-packages/system-activities/playbooks/get-asset-wrong-activity-type.md`
(the "developer selected the wrong activity when building the
workflow" branch, or the inverse "asset type was changed in
Orchestrator after the workflow was built" branch — both produce the
same error signature).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | synthesized UiPath project — same scaffold as `getasset-permission-denied` with `AssetName` changed to `ApiBaseUrl` (which exists but is a Text asset) |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

> **Note on fixtures.** Like sibling scenarios, fixtures here were
> authored from the documented playbook signature rather than captured
> from a real `.local/investigations/` session. Regenerate via
> `_shared/scripts/generate_scenario.py` from a real failed-job
> session before treating this test's score as a regression signal.

## How this differs from sibling scenarios

| Dimension | `name-mismatch` | `folder-scope-mismatch` | `permission-denied` | `wrong-activity-type` (this) |
|---|---|---|---|---|
| `AssetName` | typo | correct | correct | correct |
| `FolderPath` | real folder | non-existent | real folder | real folder |
| Asset visible in folder asset list? | no (different name) | n/a | yes | **yes (but wrong type)** |
| Asset type matches activity type? | n/a | n/a | yes | **no — Text vs Credential** |
| HTTP status / error code | 404 / 1002 | 403 / 1100 | 403 / 0 | **400 / "Invalid asset type"** |
| Error message anchor | "Could not find the asset" | "Folder ... does not exist" | "You are not authorized" / "required permissions on Assets" | "does not work with assets of type" / "Invalid asset type" |
| Matched playbook | `get-asset-not-found.md` | `get-asset-folder-scope-mismatch.md` | `get-asset-permission-denied.md` | `get-asset-wrong-activity-type.md` |

This scenario forces the agent past three rule-outs (asset exists,
folder exists, permission is fine — the error isn't 403/code 0) before
landing on the type mismatch. The asset list fixture is the decisive
signal: it shows `ApiBaseUrl` is present with `ValueType: "Text"`,
which contradicts the `Get Credential` activity's expectation.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook AND reached the same root cause as `RESOLUTION.md`
- Conclusion must name BOTH the activity (`Get Credential` / `GetRobotCredential`) AND the asset's actual type (`Text`) and explain that they are incompatible

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name getasset-wrong-activity-type --apply
```
