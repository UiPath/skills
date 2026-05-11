# Get Asset Failure — Folder Scope Mismatch

This scenario reproduces a runtime `Get Credential` failure caused by a
`FolderPath` property pointing to a folder that does not exist in the
tenant. Orchestrator returns error code **1100** ("Folder does not
exist or the user does not have access to the folder").

## What this scenario uncovers

**Root Cause:** The `Get Credential` activity in `Main.xaml` has
`FolderPath="OldDevFolder"`. The tenant folders list returns only
`Remote Debugging` (where the job actually runs) and `Shared` — there
is no folder named `OldDevFolder`. Orchestrator cannot resolve the
asset because the targeted folder does not exist.

This maps to:
`references/activity-packages/system-activities/playbooks/get-asset-folder-scope-mismatch.md`
(the "OrchestratorFolderPath set to a wrong or nonexistent folder" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | synthesized UiPath project — derived from the `getasset-name-mismatch` scenario with `AssetName` fixed (correct spelling) and `FolderPath` mutated to a non-existent folder |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

> **Note on fixtures.** Like `getasset-name-mismatch`, fixtures here
> were authored from the documented playbook signature rather than
> captured from a real `.local/investigations/` session. Regenerate via
> `_shared/scripts/generate_scenario.py` from a real failed-job
> session before treating this test's score as a regression signal.

## Why this is different from `getasset-name-mismatch`

| Dimension | `getasset-name-mismatch` | `getasset-folder-scope-mismatch` |
|---|---|---|
| AssetName property | typo (`myHiddenAset`) | correctly spelled (`myHiddenAsset`) |
| FolderPath property | matches a real folder (`Remote Debugging`) | points to a non-existent folder (`OldDevFolder`) |
| Orchestrator error code | **1002** (asset not found) | **1100** (folder doesn't exist / no access) |
| Playbook | `get-asset-not-found.md` | `get-asset-folder-scope-mismatch.md` |

Both scenarios use the same `Get Credential` activity shape, so they
exercise the diagnostic agent's ability to discriminate between
adjacent failure modes — name-level vs folder-level lookup failure.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-diagnostics` skill
- Agent matched the correct playbook AND reached the same root cause as `RESOLUTION.md`
- Specifically, the agent must name `OldDevFolder` and confirm it does not exist in the tenant's folder list

## Regenerating from a real session

```bash
python tests/tasks/uipath-diagnostics/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name getasset-folder-scope-mismatch --apply
```
