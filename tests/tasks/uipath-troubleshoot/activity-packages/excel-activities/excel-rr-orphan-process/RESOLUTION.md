# Final Resolution

---

**Root Cause:** The prior run of `ExcelDailyImport` (key
`dd444444-5555-6666-7777-888899990000`) left an orphan `EXCEL.EXE`
process running under the Robot user's session on `MOCK-HOST`. The
orphan still holds the file lock on
`C:\Robot\Data\sales-2026-05.xlsx`. The current run (key
`cc333333-4444-5555-6666-777788889999`) tried to open the same
workbook and the OS refused with `IOException`.

The orphan was produced by the workflow itself. `Main.xaml` has:

- `Excel Application Scope` with `ContinueOnError="True"`
  (`ExcelApplicationScope_1`).
- A `TryCatch` (`TryCatch_1`) wrapping the scope's body. The `Catch`
  handler only logs the exception — it does not re-throw and does not
  dispose the scope.

Together, these mean that when an activity inside the scope throws
(in the prior run: a NullReferenceException while parsing a malformed
cell), the exception is swallowed and the `Excel Application Scope`
never reaches its disposal path. The COM-launched `EXCEL.EXE`
continues running under the Robot user's session after the workflow
ends.

**What went wrong:**

- Prior job `dd444444-...` started at `2026-05-19T07:50:00.500Z` and
  faulted at `2026-05-19T07:50:04.200Z` with
  `System.NullReferenceException` thrown by an activity inside the
  Excel scope. State history: `Running → Faulted` (no Stopping /
  Killing — clean workflow-level fault). The Robot service tore down
  the executor; the un-disposed `EXCEL.EXE` survived.
- Current job `cc333333-...` started 10 minutes later at
  `2026-05-19T08:00:01.300Z` (next scheduled run). Its `Use Excel File`
  scope tried to open the same workbook and hit `IOException` from
  the lock held by the orphan.
- `or jobs list` for the folder shows only those two jobs in the
  window — no concurrent sibling, no overlapping schedules.
- `or triggers list` returns a single trigger
  (`HourlySalesA`, cron `0 0/30 * * * ?`).

**Why:** When `ContinueOnError="True"` is set on `Excel Application
Scope` and a `TryCatch` swallows scope-internal exceptions, the scope
never reaches its disposal path on the unhappy path. `EXCEL.EXE` is
launched by the scope via COM; nothing else closes it. The next run
inherits the orphan and faults at file acquisition.

---

**Evidence:**

### Orchestrator (Root cause)
- Current job: `ExcelDailyImport` (key `cc333333-...`) — Faulted at
  `2026-05-19T08:00:01.812Z`. Error:
  `System.IO.IOException: The process cannot access the file
  'C:\Robot\Data\sales-2026-05.xlsx' because it is being used by
  another process.`
- Prior job: `ExcelDailyImport` (key `dd444444-...`) — Faulted at
  `2026-05-19T07:50:04.200Z`. Error:
  `System.NullReferenceException: Object reference not set to an
  instance of an object.` Thrown inside `ExcelApplicationScope_1`.
- Both jobs ran on the same host (`MOCK-HOST`) under the same Robot
  user (`UIPATH\AUTOMATION1`), against the same workbook
  (`C:\Robot\Data\sales-2026-05.xlsx`).
- Single active trigger (`HourlySalesA`) on `0 0/30 * * * ?`. No
  overlap pattern.

### Workflow Source (Root cause)
- `process/Main.xaml`: `<uix:ExcelApplicationScope ...
  ContinueOnError="True" Visible="True" ...>` — the COM-launched
  Excel UI is visible (more likely to be left stranded) AND the scope
  is set to swallow errors.
- `process/Main.xaml`: `<TryCatch ...>` whose `Catch` is a single
  `LogMessage` with no re-throw and no scope disposal.

### Cross-check — what this is NOT
- Not concurrent jobs (no overlapping job windows; single trigger).
- Not a user-Excel-UI-open (unattended host, no human-owned
  `EXCEL.EXE`).
- Not a network-share lock (local `C:\Robot\Data\` path).
- Not an AV/EDR transient hold (lock is persistent across the 10-
  minute gap between jobs and across every subsequent run).

---

**Recommended Fix (Resolution):**

### One-off cleanup

On `MOCK-HOST` as the Robot user (or as admin with Robot session ID):

```powershell
Get-Process EXCEL -ErrorAction SilentlyContinue |
  Where-Object { $_.UserName -eq 'UIPATH\AUTOMATION1' } |
  Stop-Process -Force
```

Confirm the lock is released:

```powershell
handle.exe -a 'C:\Robot\Data\sales-2026-05.xlsx'
```

Then re-trigger the job to verify it now succeeds.

### Permanent workflow fix (load-bearing)

In `Main.xaml`:

1. Remove `ContinueOnError="True"` from `ExcelApplicationScope_1`.
   The scope must propagate its exceptions so its disposal runs.
2. Fix the `TryCatch_1` Catch handler: either re-throw the exception
   (`<Rethrow />`) after logging, or restructure so the Catch does
   not wrap the scope (move the Try Catch inside the scope's body
   instead of around it).
3. Set `Visible="False"` on the scope unless interactive debugging is
   required. A non-visible instance is easier to clean up after an
   abrupt executor exit.
4. Strongly recommended: migrate from `Excel Application Scope` to
   `Use Excel File`. The modern scope uses the OpenXML provider by
   default and has more robust disposal semantics — no COM-launched
   `EXCEL.EXE` to leak.

### Defensive pre-job cleanup

Until the workflow fix is deployed, add a pre-job activity (or a
Robot host startup task) that kills stale `EXCEL.EXE` under the Robot
user before each workflow run. Idempotent and cheap.

**Prevention:** Never set `ContinueOnError="True"` on an Excel scope
in production. Never wrap an Excel Application Scope in a Try Catch
whose Catch only logs — either re-throw or restructure so the scope
disposes cleanly. Default to `Use Excel File` for new workflows.
Audit existing projects for these patterns.
