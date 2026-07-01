# Get Asset Failure — Name Mismatch (Typo)

This scenario reproduces a runtime `Get Credential` failure caused by an
**AssetName typo** in the workflow XAML. Orchestrator returns HTTP 404 /
error code 1002 because the asset literally named in the activity does
not exist — but a near-miss asset with the corrected spelling does
exist in the same folder.

## What this scenario uncovers

**Root Cause:** The `Get Credential` activity in `Main.xaml` references
`AssetName="myHiddenAset"` (missing an "s"). The intended asset in the
`Remote Debugging` folder is `myHiddenAsset`. Orchestrator's exact-match
asset lookup returns 404.

This maps to:
`references/activity-packages/system-activities/playbooks/get-asset-not-found.md`
(specifically the "case or spelling difference" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | snapshot of the failing UiPath project (`Main.xaml` + `project.json` from `C:\Temp\GetAsset Scenarios\name mismatch`) |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

> **Note on fixtures.** Unlike `rpa-preflight-failure` and
> `faulted_excel_o365`, the fixtures here were authored from the
> documented playbook signature rather than captured from a real
> `.local/investigations/` session. Before treating this test's score
> as a regression signal, replay against a real failed job and
> regenerate via `_shared/scripts/generate_scenario.py` — see
> `tests/tasks/uipath-troubleshoot/CLAUDE.md`.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook AND reached the same root cause as `RESOLUTION.md`
- Specifically, the agent must name the typo (`myHiddenAset` vs `myHiddenAsset`), not just "asset missing"

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name getasset-name-mismatch --apply
```
