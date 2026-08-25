# Classic Invoke Workflow File — Invoked Workflow Excluded from Package (Runtime FileNotFound)

Runtime troubleshooting scenario for `UiPath.Core.Activities.InvokeWorkflowFile`.

## What this scenario exercises

The process runs in Studio but a robot job faults with `System.IO.FileNotFoundException` at the Invoke
Workflow File. The invoked `Helpers\CalculateTax.xaml` is present in the project source but listed in
`project.json` `designOptions.processOptions.ignoredFiles`, so it is excluded from the published
package and missing on the robot. The agent must find the `ignoredFiles` exclusion and fix it.

Distinct from the design-time `classic-invoke-file-not-packed` scenario (invoked `.xaml` **outside** the
project root): here the file is **inside** the project but **explicitly excluded** from packing, and the
failure surfaces only at **run time** on the robot.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` | shared manifest-driven mock dispatcher from `../../_shared/mock_template/` |
| `process/` | crafted project source: `Main.xaml` invokes `Helpers\CalculateTax.xaml` (present); `project.json` lists that file in `ignoredFiles` |
| `data/m/r/*.json` | faulted-job fixtures (`jobs get`/`logs`/`history`/`traces`, `folders`/`jobs list`) carrying the runtime `FileNotFoundException` at `InvokeWorkflowFile.LoadWorkflow` |
| `data/m/r/manifest.json` | `docsai ask` passthrough + job/folder rules + permissive empty `unmocked_default` |

## Success criteria

Scores the **conclusion**, not the trajectory (`skill_triggered` + `llm_judge` against `RESOLUTION.md`):

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the `ignoredFiles` package exclusion and the fix (remove it, re-publish).

Playbook: `references/activity-packages/classic-activities/playbooks/invoke-workflow-failed.md`
(workflow-file-missing / not-packed branch).
