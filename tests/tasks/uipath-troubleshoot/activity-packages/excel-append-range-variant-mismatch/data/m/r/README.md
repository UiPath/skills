# Excel Append Range — Activity Variant Mismatch (Missing Scope)

This scenario reproduces an Append Range failure where the Modern
`AppendRangeX` activity is placed at the workflow's root without an
enclosing `Use Excel File` container. The job ends with:

```
UiPath.Excel.BusinessException: The 'Append Range' activity must be placed inside a 'Use Excel File' container, which manages the workbook context for the activity.
```

## What this scenario uncovers

**Root Cause:** The workflow's Append Range activity is the Modern
`AppendRangeX` surface, which requires a `Use Excel File` scope to
provide workbook context. In `Main.xaml` the activity sits at the
workflow's root — no surrounding scope. Scope validation detects the
missing container and throws before any provider call.

The fix branches on the deployment context: if the Robot host has
Excel installed, wrap in `Use Excel File`; if not, switch surface to
the standalone `Append Range Workbook` activity.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/append-range-failures.md`
(the "Activity variant mismatch" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelPayrollProcess` project — `Invoke BuildPayrollRows.xaml` → `AppendRangeX` activity at the root with no enclosing scope |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; the `or jobs logs` Trace entries capture the scope-validation log line that explicitly names the missing container, and the BusinessException wording names "Use Excel File" as the required scope |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (BusinessException naming
the missing scope) → `jobs logs` (scope-validation Trace + the
BusinessException) → workflow source review (confirms no `Use Excel
File` wraps the AppendRange activity) → conclude branch 1.

> **Note on the deployment-context fork.** The fix has two viable
> primary paths depending on whether Excel is installed on the
> Robot host. The test grades agents that recognize this fork
> and recommend the appropriate fix (or, more rigorously, ask the
> user about the host's Excel availability before picking one).
> Agents that recommend "just switch to Workbook" without
> considering host context get partial credit — Workbook is a
> legitimate alternative, but switching without understanding
> the surface differences is the playbook's anti-pattern.

> **Note on fixtures.** Synthetic. The HR sub-workflow, DataTable
> shape, and exact BusinessException wording are placeholders. The
> test grades whether the agent identifies the missing scope as the
> root cause and recommends a structural fix (wrap in scope, or
> switch surface with host-context awareness).
