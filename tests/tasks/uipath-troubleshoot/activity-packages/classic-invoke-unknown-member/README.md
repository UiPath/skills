# Classic Invoke Workflow File — Unknown Member `ArgumentsVariable` (Design-Time)

Design-time (Studio compile) troubleshooting scenario for `UiPath.Core.Activities.InvokeWorkflowFile`.

## What this scenario exercises

Studio reports `Cannot set unknown member
'UiPath.Core.Activities.InvokeWorkflowFile.ArgumentsVariable'` when opening the project. The agent must
recognize this as a **package-version mismatch**: `Main.xaml` serializes an `ArgumentsVariable` member
on the invoke, but `project.json` pins an older `UiPath.System.Activities` (`[22.10.4]`) that has no
such property.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` | shared manifest-driven mock dispatcher from `../../_shared/mock_template/` |
| `process/` | crafted project source: `project.json` (old package pin) + `Main.xaml` (invoke with `ArgumentsVariable`) + `CalculateTotals.xaml` (present child) |
| `data/m/r/manifest.json` | `docsai ask` passthrough + permissive empty `unmocked_default` — no job/trace exists for a design-time compile error |

## Success criteria

Scores the **conclusion**, not the trajectory (`skill_triggered` + `llm_judge` against `RESOLUTION.md`):

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the package-version mismatch and the fix (align `UiPath.System.Activities`, Import
  Arguments).

Playbook: `references/activity-packages/classic-activities/playbooks/invoke-workflow-file-design-time-errors.md`.
