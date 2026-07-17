# Classic Invoke Workflow File — Required Argument Not Supplied (Design-Time)

Design-time validation troubleshooting scenario for `UiPath.Core.Activities.InvokeWorkflowFile`.

## What this scenario exercises

Validation fails on the parent workflow with `Value for a required activity argument was not supplied`,
pointing at the Invoke Workflow File. The agent must recognize that the invoked workflow gained a new
required `In` argument (`in_ArchivePath`) that the parent's invoke never mapped, and prescribe **Import
Arguments**.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` | shared manifest-driven mock dispatcher from `../../_shared/mock_template/` |
| `process/` | crafted project source: `ArchiveInvoice.xaml` declaring two required inputs; `Main.xaml` invoking it but mapping only one |
| `data/m/r/manifest.json` | `docsai ask` passthrough + permissive empty `unmocked_default` |

## Success criteria

Scores the **conclusion**, not the trajectory (`skill_triggered` + `llm_judge` against `RESOLUTION.md`):

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the unmapped required argument and the fix (Import Arguments, map `in_ArchivePath`).

Playbook: `references/activity-packages/classic-activities/playbooks/invoke-workflow-file-design-time-errors.md`.
