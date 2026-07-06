# Excel Read Range — Broken Named Range (#REF!)

This scenario reproduces a Read Range failure where the workflow
references a named range (`Range: "MyDataRange"`), the workbook
opens successfully, sheet enumeration succeeds, but the named-range
lookup fails because the named range's `Refers to` in Name Manager
is `#REF!`. The job ends with:

```
System.NullReferenceException: Object reference not set to an instance of an object.
```

(no cell pointer).

## What this scenario uncovers

**Root Cause:** The workbook's defined name `MyDataRange` previously
pointed at `Sheet1!A1:E1000`, but `Sheet1` was deleted or restructured
upstream. The named range's reference is now `#REF!`. The workflow's
Read Range with `Range: "MyDataRange"` looks up the name in the
workbook's defined-names collection, gets a broken-reference target,
and throws `NullReferenceException` from inside the activity's
range-resolution code.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/read-range-null-reference.md`
(the "Broken named range / formula reference" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelDailyImport` project — `Use Excel File` → `Get Workbook Sheets` (succeeds) → `Read Range "MyDataRange"` (NRE) |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; the `or jobs logs` Trace entry from `Read Range` includes the named-range lookup attempt with the broken refers-to value |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (bare NRE) → `jobs logs`
(Get Workbook Sheets succeeded; Read Range Trace shows named-range
lookup with `RefersTo: #REF!`) → workflow source (named-range Range
property) → conclude branch 3.

> **Note on fixtures.** Synthetic. The named range `MyDataRange`
> and the broken refers-to are placeholders. The test grades
> whether the agent surfaces the named-range branch using the
> workflow-source + log evidence.
