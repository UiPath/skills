# Excel Read Range — File Locked, CLI Evidence Insufficient

This scenario reproduces an `ExcelReadRange` failure where the workbook
is locked by SOMETHING, but the `uip` CLI evidence does NOT pinpoint
which cause-branch applies. The agent must recognize the boundary of
CLI evidence and recommend a host-side investigation rather than
guessing.

The job ends with:

```
System.IO.IOException: The process cannot access the file 'C:\Robot\Data\sales-2026-05.xlsx' because it is being used by another process.
```

## What this scenario uncovers

**Expected outcome:** The agent matches the
`activity-packages/excel-activities/playbooks/read-range-file-locked.md`
playbook AND tells the user the lock holder cannot be identified
through Orchestrator alone — they need to capture host-side evidence
(`Get-Process EXCEL`, Sysinternals `handle.exe -a <path>`, and
`Get-SmbOpenFile` if the workbook is on a UNC path).

**The branches that COULD apply** without further evidence:

- User opened the workbook in Excel UI (branch 1)
- Hidden Excel instance under a different user session (branch 6)
- Network-share lock from a different host (branch 3) — only if the
  workbook is on a UNC path
- Antivirus / EDR / Windows Search / sync client transient hold
  (branch 5)

**The branches that are ruled OUT by the CLI evidence:**

- Concurrent Robot jobs (branch 4) — `or jobs list` shows no
  concurrent sibling and `or triggers list` shows a single non-
  overlapping trigger.
- Orphan EXCEL.EXE from a prior run of this workflow (branch 2) — no
  prior faulted runs in the recent window, and `process/Main.xaml`
  has no `ContinueOnError` on the scope and no swallowing TryCatch.

The agent must NOT guess between the remaining branches without
host-side evidence. Confident guessing is the failure mode this test
catches.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | `ExcelDailyImport` project where `Main.xaml` is clean — no `ContinueOnError`, no swallowing TryCatch, modern `Use Excel File` scope |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored so the agent can rule out concurrent / orphan branches but cannot identify a positive cause |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The expected investigation chain: `folders list-current-user` → `jobs
list --state Faulted` → `jobs get` → `jobs logs` → `jobs list`
(broader, returns only this single failure, no siblings, no prior
fails) → `triggers list` (single trigger) → workflow source review
(clean) → STOP. At this point CLI evidence is exhausted. The agent
must explicitly name the host-side commands and ask the user to run
them.

> **Note on fixtures.** Synthetic. The job key, folder key, and
> workbook path are placeholders. What the test grades is the agent's
> awareness of evidence-availability boundaries.
