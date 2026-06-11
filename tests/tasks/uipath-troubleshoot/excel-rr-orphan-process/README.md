# Excel Read Range — File Locked by Orphan EXCEL.EXE From Prior Job

This scenario reproduces an `ExcelReadRange` failure caused by **an
orphan EXCEL.EXE process left behind by the previous run of the same
process**. The job ends with:

```
System.IO.IOException: The process cannot access the file 'C:\Robot\Data\sales-2026-05.xlsx' because it is being used by another process.
```

## What this scenario uncovers

**Root Cause:** The prior run of `ExcelDailyImport` (key
`dd444444-...`) ran 10 minutes earlier and faulted with a workflow
exception **inside** the `Excel Application Scope`. Because the scope
was authored with `ContinueOnError="True"` AND wrapped in a `Try Catch`
whose `Catch` swallowed the exception without disposing the scope, the
COM-launched `EXCEL.EXE` process was left running under the Robot
user's session. It still holds the workbook's file lock when the
current job (key `cc333333-...`) tries to open the same workbook.

This is NOT a concurrent-jobs failure — there is only one trigger and
no sibling job is running. The CLI evidence chain is:

- `or jobs list` shows the prior faulted run + the current run, no
  overlap.
- Workflow source (`process/Main.xaml`) has
  `ContinueOnError="True"` on the Excel Application Scope and a Try
  Catch that does not re-throw.

Together they pinpoint the orphan-process branch.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/excel-activities/playbooks/read-range-file-locked.md`
(the "Orphan EXCEL.EXE from a prior job" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | `ExcelDailyImport` project where `Main.xaml` deliberately has `ContinueOnError="True"` on `ExcelApplicationScope` AND a `TryCatch` whose `Catch` only logs without re-throwing |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The expected investigation chain: `folders list-current-user` → `jobs
list --state Faulted` → `jobs get` (current) → `jobs logs` → `jobs
list` (broader, surfaces the prior faulted run) → `jobs get <prior-key>`
→ `triggers list` (single trigger, no overlap) → workflow source
inspection.

> **Note on fixtures.** Like the sibling scenarios, fixtures are
> synthetic. The job keys, folder key, workbook path, and trigger
> name are placeholders — the test grades whether the agent surfaces
> the orphan-process branch with BOTH pieces of evidence (prior
> faulted job + `ContinueOnError="True"` in workflow source), not
> the specific names.
