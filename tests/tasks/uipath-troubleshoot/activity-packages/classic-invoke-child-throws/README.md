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
| `process/` | crafted project source: `Main.xaml` invoking `ProcessPayments.xaml`; the child dereferences an uninitialized `lineItems` list |

## Success criteria

Scores the **conclusion**, not the trajectory (`skill_triggered` + `llm_judge` against `RESOLUTION.md`):

- Agent invoked the `uipath-troubleshoot` skill.
- Agent attributed the fault to the child workflow's uninitialized-list NRE (not the invoke) and fixed
  the child.

Playbook: `references/activity-packages/classic-activities/playbooks/invoke-workflow-failed.md` (runtime
"child workflow threw" branch).

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's UID/GID-isolated mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
