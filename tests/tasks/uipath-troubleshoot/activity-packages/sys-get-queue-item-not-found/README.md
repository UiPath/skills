# Get Queue Item Failure — Queue Does Not Exist

This scenario replays a real faulted Orchestrator job where the
`Get Queue Item` activity references a queue that does not exist in the
folder where the job runs. Orchestrator returns HTTP 404 / error code
1002 (`OrchestratorHttpException`), surfaced under the generic "HTTP
Error" job header.

## What this scenario uncovers

**Root Cause:** The queue `OrdersToProcess` does not exist in the
`Finance` folder. `Get Queue Item` calls Orchestrator and gets HTTP 404
/ error code 1002 (`OrdersToProcess does not exist`). Despite the generic
"HTTP Error / Check HTTP connectivity" header, the response body names
the missing queue — this is not a connectivity problem.

This maps to:
`references/activity-packages/system-activities/playbooks/queue-transaction-activity-failed.md`
(the 404 / "does not exist. Error code: 1002" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | snapshot of the failing UiPath project (`Main.xaml` + `project.json`) |
| `fixtures/mocks/responses/*.json` | canned `uip` responses replaying the captured job/logs |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook AND reached the same root cause as `RESOLUTION.md`
- Specifically, the agent must name the missing queue `OrdersToProcess` in the Finance folder (404 / code 1002), NOT a generic HTTP connectivity failure
