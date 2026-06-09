# Excel Write Cell — Loop-Induced "Excel Is Busy"

This scenario reproduces a Write Cell failure that emerges only
after N successful iterations inside a `For Each Row` loop. The
job ends with the canonical:

```
UiPath.Excel.BusinessException: The data you want to write has a wrong format, or Excel is busy.
```

— same wording as branch 2 (formula syntax) but with the "Excel
is busy" clause actually applicable here.

## What this scenario uncovers

**Root Cause:** The workflow's `Write Cell` activity is nested
inside a `For Each Row` loop. Each iteration opens the workbook,
writes one cell, saves, and closes the file. After N iterations
(247 in this job, different on retry) Excel COM state becomes
corrupt — COM-object leaks accumulate, the file-lock churn races
with itself, and the activity faults.

The "or Excel is busy" clause of the error is misleading on
branch 2 (formula syntax — nothing is busy) but ACCURATE on
branch 3: Excel COM is in a degraded state from the open/save/
close churn.

**Critical disambiguation from branch 2:** the same error wording
is produced by formula syntax errors. The distinguishing evidence
is workflow context + execution pattern:

| Signal | Branch 2 (formula syntax) | Branch 3 (loop thrash) |
|---|---|---|
| Workflow source | Single Write Cell, no loop | Write Cell inside For Each (Row) |
| Failure pattern | Fails on first iteration, deterministic | N iterations succeed, then fails; N varies between runs |
| User context | "Single activity, no loop" | "Hundreds of rows wrote before failure" |
| Job logs | One Write Cell attempt, fails | Many successful Write Cell invocations preceding the failure |

This maps to **branch 3 (loop-induced Excel-is-busy / COM thrash)**
in:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/write-cell-failures.md`

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelWriteCellProcess` project — `Use Excel File` scope opens the workbook, `Read Range` populates a DataTable, then `For Each Row` iterates the table writing one cell per row via `Write Cell` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; the `or jobs get` Info field is the BusinessException; `or jobs logs` shows ~247 successful Write Cell iterations preceding the failure |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` (BusinessException
identical to branch 2) → `jobs logs` (**N successful Write Cell
iterations**, then fault on iteration N+1 — the partial-success
pattern is the smoking gun) → **workflow source review** (For Each
Row + Write Cell inside) → conclude branch 3, recommend bulk
Read Range → DataTable → Write Range pattern.

> **Note on fixtures.** Synthetic. The exact iteration count (247),
> column names, and workbook structure are placeholders. The test
> grades whether the agent:
>
> 1. Notices the partial-success pattern in job logs (rules out
>    branch 2).
> 2. Identifies the For Each Row + Write Cell-inside pattern in the
>    workflow source (positive signal for branch 3).
> 3. Recommends the bulk pattern fix — NOT Retry Scope, Delay,
>    or formula-syntax changes (all documented anti-patterns).
