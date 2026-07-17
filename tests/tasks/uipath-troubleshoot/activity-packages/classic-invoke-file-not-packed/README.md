# Classic Invoke Workflow File — Invoked Workflow Not Packed (FileNotFound)

Design-time / packaging troubleshooting scenario for `UiPath.Core.Activities.InvokeWorkflowFile`.

## What this scenario exercises

The project runs in Studio but fails on publish/run with `System.IO.FileNotFoundException: Cannot find
the file 'EmailHelper.xaml'`. The agent must recognize that the invoked `.xaml` lives **outside the
project root** (`..\Shared\EmailHelper.xaml`) and is therefore not included in the package.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` | shared manifest-driven mock dispatcher from `../../_shared/mock_template/` |
| `process/` | crafted project source: `Main.xaml` invoking `..\Shared\EmailHelper.xaml` (a path escaping the project root); the invoked file is absent from the project |
| `data/m/r/manifest.json` | `docsai ask` passthrough + permissive empty `unmocked_default` |

## Success criteria

Scores the **conclusion**, not the trajectory (`skill_triggered` + `llm_judge` against `RESOLUTION.md`):

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the out-of-project invoked workflow and the fix (move it inside the project, repoint
  the invoke).

Playbook: `references/activity-packages/classic-activities/playbooks/invoke-workflow-file-design-time-errors.md`.
