# Excel Write Cell — Formula Syntax (Semicolon Separators)

This scenario reproduces a Write Cell failure where the configured
`Value` is a formula using semicolon parameter separators
(`=SUM(A1;A10)`) instead of the comma separators UiPath / Excel COM
require regardless of host regional setting. The job ends with:

```
UiPath.Excel.BusinessException: The data you want to write has a wrong format, or Excel is busy.
```

## What this scenario uncovers

**Root Cause:** UiPath passes the formula string to Excel COM
verbatim, and Excel COM requires comma separators in parameter
lists regardless of the host's Windows regional setting. The Excel
UI displays semicolons in non-US locales (so workflow authors who
copy formulas from Excel see semicolons and assume they're valid),
but the COM API does not accept them. The formula `=SUM(A1;A10)`
fails to parse, and Excel surfaces the canonical "wrong format, or
Excel is busy" BusinessException.

**Critical disambiguation:** branch 3 (loop-induced Excel COM
thrash) produces the SAME error wording. The distinguishing
evidence is workflow context:
- This scenario: a single Write Cell with a formula Value, NOT
  inside a loop. The user explicitly states "no loop, no parallel
  work, no other Excel jobs."
- Branch 3: a Write Cell inside a tight loop where N iterations
  succeed before the failure.

Without checking the workflow source for the formula content AND
the loop context, an agent could pick the wrong branch and
recommend the wrong fix.

This maps to **branch 2 (formula syntax rejected)** in:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/write-cell-failures.md`

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelWriteCellProcess` project — `Use Excel File` scope with a single nested `Write Cell` activity whose `Value` is `"=SUM(A1;A10)"` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; the `or jobs get` Info field is the BusinessException; `or jobs logs` shows the scope opened successfully, then the Write Cell faulted on the first (and only) attempt |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (BusinessException wording
identical to branch 3) → `jobs logs` (single Write Cell invocation,
not a sequence of successful iterations) → **workflow source review**
(formula with semicolons + NOT inside a loop = branch 2) → conclude
branch 2, recommend replacing semicolons with commas.

> **Note on fixtures.** Synthetic. The formula and job key are
> placeholders. The test grades whether the agent reads the
> workflow source, identifies the semicolon separator, and
> contrasts with branch 3 by noting absence of loop — rather than
> reflexively recommending the loop-thrash fix (use Write Range
> instead of Write Cell) which doesn't apply here.
