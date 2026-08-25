# Excel Write Range — Uninitialized DataTable

This scenario reproduces a Write Range failure where the `DataTable`
argument was never assigned because the preceding `Read Range` is
nested inside an `If` activity whose condition evaluated to `False`.
The job ends with:

```
System.NullReferenceException: Object reference not set to an instance of an object.
```

## What this scenario uncovers

**Root Cause:** The workflow's Write Range activity receives the
`dtSource` variable, but `dtSource` was never assigned during this
run because the preceding `If File.Exists("C:\Robot\Data\customer-source.xlsx")`
evaluated to `False` and skipped its Then-branch (which contained the
populating `Read Range`). Write Range's argument resolver dereferences
the `Nothing` variable and throws the NRE before any provider call.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/write-range-failures.md`
(the "Uninitialized / null DataTable" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelExportProcess` project — `If File.Exists(...)` wrapping the populating `Read Range`, followed by an unconditional `Write Range` against `dtSource` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; the `or jobs logs` Trace entries capture both the `If` condition evaluating to `False` AND the resolver finding `dtSource = Nothing` |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (NullReferenceException on
WriteRange_1) → `jobs logs` (the If-condition-False Trace + the
DataTable-resolved-to-Nothing Trace are the smoking gun) → workflow
source review (confirms the `If` wraps the only assignment to
`dtSource`) → conclude branch 1.

> **Note on fixtures.** Synthetic. The source workbook path,
> condition expression, and exact NRE stack trace are placeholders.
> The test grades whether the agent connects the skipped-If to the
> never-assigned variable and recommends a real fix (initialize at
> declaration, guard the Write Range, fail-fast on missing source,
> or restructure the workflow to make the dependency explicit).
