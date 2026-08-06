# Classic Invoke Workflow File — Persistence Not Supported (Runtime)

Runtime troubleshooting scenario for `UiPath.Core.Activities.InvokeWorkflowFile`.

## What this scenario exercises

A robot job faults with `System.NotSupportedException` — the invoked workflow requires persistence but
the runtime does not support it. `SubmitForApproval.xaml` runs a `Run Job` in **Suspend** mode
(persistence required), while `project.json` has `runtimeOptions.supportsPersistence: false`. The agent
must connect the suspending activity to the missing persistence support and fix it (enable
`supportsPersistence`, or switch `Run Job` out of Suspend mode).

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | crafted project source: `Main.xaml` invokes `SubmitForApproval.xaml`, which runs `RunJob ExecutionMode="Suspend"`; `project.json` has `supportsPersistence: false` |

## Success criteria

Scores the **conclusion**, not the trajectory (`skill_triggered` + `llm_judge` against `RESOLUTION.md`):

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the persistence-not-supported cause and the fix (`supportsPersistence: true`, or
  drop Suspend mode).

Playbook: `references/activity-packages/classic-activities/playbooks/invoke-workflow-failed.md`
(persistence branch).

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's UID/GID-isolated mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
