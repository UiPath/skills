# Classic Invoke Workflow File — Runtime Argument Mismatch (Stale Key)

Runtime troubleshooting scenario for `UiPath.Core.Activities.InvokeWorkflowFile`.

## What this scenario exercises

A job faults at an `Invoke Workflow File` with `System.ArgumentException` — "the following keys from the
input dictionary do not map to arguments and must be removed: in_Amount". The agent must recognize
**argument-name drift**: the parent passes `in_Amount`, but the invoked `ValidatePayment.xaml` renamed
that input to `in_GrossAmount`. The invoke fails at argument binding, before the child body runs. Fix:
Import Arguments and remap to `in_GrossAmount`.

Distinct from the design-time `classic-invoke-arg-required` scenario (a Studio validation error about an
*unmapped required* argument): here the parent maps a *stale key that no longer exists* on the child,
and the failure is a **runtime** `ArgumentException`.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` | shared manifest-driven mock dispatcher from `../../_shared/mock_template/` |
| `process/` | crafted project source: `Main.xaml` invoking `ValidatePayment.xaml` with `in_Amount`; the child declares `in_GrossAmount` |
| `data/m/r/*.json` | faulted-job fixtures (`jobs get`/`logs`/`history`/`traces`, `folders`/`jobs list`) carrying the argument-binding `ArgumentException` |
| `data/m/r/manifest.json` | `docsai ask` passthrough + job/folder rules + permissive empty `unmocked_default` |

## Success criteria

Scores the **conclusion**, not the trajectory (`skill_triggered` + `llm_judge` against `RESOLUTION.md`):

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the stale-argument-key mismatch and the fix (Import Arguments, remap to
  `in_GrossAmount`).

Playbook: `references/activity-packages/classic-activities/playbooks/invoke-workflow-failed.md` (runtime
"argument name/type/direction mismatch" branch).
