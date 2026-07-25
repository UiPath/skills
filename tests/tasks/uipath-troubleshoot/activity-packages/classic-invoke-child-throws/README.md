# Classic Invoke Workflow File — Child Workflow Throws (Runtime Propagation)

Runtime troubleshooting scenario for `UiPath.Core.Activities.InvokeWorkflowFile`.

## What this scenario exercises

A job faults with `System.NullReferenceException` at an `Invoke Workflow File`. The real fault is
**inside the invoked child** (`ProcessPayments.xaml`): a `List<Double>` variable `lineItems` is used
(`.Sum()`) while null. The agent must trace **one hop into the child** and attribute the root cause
there — the invoke is only the propagation point — rather than blaming the Invoke Workflow File itself.
This tests the skill's causal-precedence / one-hop-upstream rule.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` | shared manifest-driven mock dispatcher from `../../_shared/mock_template/` |
| `process/` | crafted project source: `Main.xaml` invoking `ProcessPayments.xaml`; the child dereferences an uninitialized `lineItems` list |
| `data/m/r/*.json` | faulted-job fixtures (`jobs get`/`logs`/`history`/`traces`, `folders`/`jobs list`) whose stack localizes the fault inside the child, below the InvokeWorkflowFile frame |
| `data/m/r/manifest.json` | `docsai ask` passthrough + job/folder rules + permissive empty `unmocked_default` |

## Success criteria

Scores the **conclusion**, not the trajectory (`skill_triggered` + `llm_judge` against `RESOLUTION.md`):

- Agent invoked the `uipath-troubleshoot` skill.
- Agent attributed the fault to the child workflow's uninitialized-list NRE (not the invoke) and fixed
  the child.

Playbook: `references/activity-packages/classic-activities/playbooks/invoke-workflow-failed.md` (runtime
"child workflow threw" branch).
