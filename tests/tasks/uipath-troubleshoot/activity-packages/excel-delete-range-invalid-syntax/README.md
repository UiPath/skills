# Excel Delete Range — Invalid Range Syntax

This scenario reproduces a Delete Range failure where the activity's
`Range` property is an expression that resolves to an invalid A1
string at runtime. The job ends with:

```
System.ArgumentException: The range is invalid
```

## What this scenario uncovers

**Root Cause:** The workflow's Delete Range activity is configured
with `Range = "A1:B" + lastRow.ToString()`. The preceding Read Range
returned 0 rows from a header-only workbook, so
`lastRow = dtCleanup.Rows.Count = 0`, and the expression evaluated to
`"A1:B0"`. Row index 0 is not a legal A1 address; the Modern
`DeleteRangeX` activity's range validator rejected the string with
an `ArgumentException` before any provider call was made.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/delete-range-failures.md`
(the "Invalid range syntax or empty Range property" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelCleanupProcess` project — `Use Excel File` → `Read Range` → `Assign lastRow` → `Delete Range` with `Range = "A1:B" + lastRow.ToString()` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; the `or jobs logs` Trace entry shows the resolved expression evaluated to `"A1:B0"` immediately before the ArgumentException |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (ArgumentException
"The range is invalid" on Delete Range) → `jobs logs` (resolved
Range expression "A1:B0" with lastRow=0 is the smoking gun) →
workflow source review (confirms `Range` is a `lastRow`-dependent
expression) → conclude branch 2.

> **Note on fixtures.** Synthetic. The workbook path, row counts,
> and timing values are placeholders. The test grades whether the
> agent identifies the resolved range value as invalid A1 syntax
> and recommends either guarding the expression, switching to
> Clear Range, or using a literal range — not just observing the
> exception.
