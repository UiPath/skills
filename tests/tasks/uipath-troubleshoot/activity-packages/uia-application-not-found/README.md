# UI Automation — Application Not Found (Use Application, OpenMode=Never)

This scenario reproduces a runtime failure where a `Use Application`
(NApplicationCard) scope throws `ApplicationNotFoundException` because
its `OpenMode` is set to `Never` and the target desktop application is
not running on the robot machine.

## What this scenario uncovers

**Root Cause:** The `Use Application` scope ("Use AcmeBooks accounting
app") in `Main.xaml` has `OpenMode="Never"`. AcmeBooks.exe was not
running on the unattended robot when the job started (IT shut it down
for maintenance the prior evening and did not restart it). Because the
scope refuses to launch the app, it throws
`UiPath.UIAutomationNext.Exceptions.ApplicationNotFoundException` at
scope entry — before any inner `NClick` / `NTypeInto` executes. The
failure is **scope-level**, not selector-level.

This maps to:
`references/activity-packages/ui-automation/playbooks/application-not-found.md`
(Branch A — "Workflow assumed the app was running but OpenMode=Never
blocks the launch").

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | synthetic UiPath project — a single `Main.xaml` containing the failing `Use Application` scope with `OpenMode="Never"` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

> **Note on fixtures.** These fixtures were authored from the
> documented playbook signature — `ApplicationNotFoundException` thrown
> by `NApplicationCard` when `OpenMode=Never` and the target app is
> absent. Regenerate via `_shared/scripts/generate_scenario.py` from a
> real failed-job session before treating this test's score as a
> regression signal.

## Why this is different from selector-failure scenarios

| Dimension | `rpa-selector-healing-disabled` (selector) | `uia-application-not-found` (scope) |
|---|---|---|
| Exception | `SelectorNotFoundException` / `UiElementNotFoundException` | `ApplicationNotFoundException` |
| Faulted activity | element-level (`NClick`, `NTypeInto`) | scope-level (`NApplicationCard` / `Use Application`) |
| Where the failure originates | UI tree element lookup | Scope tries to attach to an application window |
| Fix domain | Selector / Healing Agent | `OpenMode` property on the scope |
| Playbook | `selector-failure-*.md` | `application-not-found.md` |

The two failures look superficially similar (both are "UI automation
broke and the agent should consult a UI Automation playbook"), so this
scenario exercises the troubleshooting agent's ability to discriminate
between scope-level and element-level UI automation failures.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the `application-not-found` playbook AND identified
  `OpenMode="Never"` in `Main.xaml` as the gating condition
- Specifically, the agent must:
  - Name `ApplicationNotFoundException` (not a generic selector failure)
  - Locate the `Use Application` / `NApplicationCard` scope in `Main.xaml`
  - Identify `OpenMode="Never"` as the cause
  - Recommend switching `OpenMode` to `IfNotOpen` (or equivalent)

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name uia-application-not-found --apply
```
