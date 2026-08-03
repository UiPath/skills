# Classic Invoke Workflow File — Invalid Isolated / Target-Session Combination (Runtime)

Runtime troubleshooting scenario for `UiPath.Core.Activities.InvokeWorkflowFile`.

## What this scenario exercises

A job faults with `System.Activities.InvalidWorkflowException` at the Invoke Workflow File's
`CacheMetadata`. The invoke sets `TargetSession="PictureInPicture"` (non-`Current`) while `UnSafe`
(Isolated) is `False` — a combination the runtime rejects (a non-`Current` session requires isolated
execution). The agent must identify the invalid session/isolation combo and fix it (`UnSafe=True`, or
revert `TargetSession` to `Current`).

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` | shared manifest-driven mock dispatcher from `../../_shared/mock_template/` |
| `process/` | crafted project source: `Main.xaml` invokes `GenerateReport.xaml` with `UnSafe="False"` + `TargetSession="PictureInPicture"` |
| `data/m/r/*.json` | faulted-job fixtures (`jobs get`/`logs`/`history`/`traces`, `folders`/`jobs list`) carrying the validation error at `InvokeWorkflowFile.CacheMetadata` |
| `data/m/r/manifest.json` | `docsai ask` passthrough + job/folder rules + permissive empty `unmocked_default` |

## Success criteria

Scores the **conclusion**, not the trajectory (`skill_triggered` + `llm_judge` against `RESOLUTION.md`):

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the invalid `TargetSession`/`UnSafe` combination and the fix.

Playbook: `references/activity-packages/classic-activities/playbooks/invoke-workflow-failed.md`
(isolated/elevated/target-session branch).
