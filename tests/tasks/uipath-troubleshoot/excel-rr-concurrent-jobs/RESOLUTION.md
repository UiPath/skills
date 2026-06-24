# Final Resolution

---

**Root Cause:** Two Orchestrator jobs of the same process
(`ExcelDailyImport`) ran concurrently against the same workbook
(`C:\Robot\Data\sales-2026-05.xlsx`) on the same host. The first job
acquired the file lock; the second job's `Read Range` failed with
`System.IO.IOException: The process cannot access the file ... because
it is being used by another process.` Two Orchestrator triggers
(`HourlySalesA` and `HourlySalesB`) fire the same process every 30
minutes from the same start time, so every firing has overlapping
Running windows.

**What went wrong:** Failing job `aa111111-2222-3333-4444-555566667777`
started at `2026-05-19T08:00:01.300Z`. Sibling job
`bb222222-3333-4444-5555-666677778888` started ~800 ms earlier at
`2026-05-19T08:00:00.500Z` and was still Running when the second one
opened the workbook. The second `Read Range` activity tried to acquire
the file lock and the OS refused with `IOException`. The job state
history shows a clean `Running -> Faulted` transition (no operator
action). `or triggers list` confirms the two triggers fire on
overlapping schedules.

**Why:** Excel COM (and the OpenXML provider in default mode) opens
workbooks with exclusive write access. When two processes try to open
the same file simultaneously, the second loses. The Orchestrator
trigger configuration here guarantees the race — both triggers fire
on the same 30-minute cycle from the same start time, so the Running
windows of the two job firings always overlap. The workbook's lock
holder is the first-to-start; whichever started later faults.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelDailyImport` (key `aa111111-...`) — Faulted at
  `2026-05-19T08:00:01.800Z` after ~500 ms of `Running`
- Folder: `ExcelImports` (key `f0011111-2222-3333-4444-555566667777`)
- Host: `MOCK-HOST`, runtime type `Unattended`
- Error (verbatim from `or jobs get`):
  `System.IO.IOException: The process cannot access the file 'C:\Robot\Data\sales-2026-05.xlsx' because it is being used by another process.`
- Sibling job: `ExcelDailyImport` (key
  `bb222222-3333-4444-5555-666677778888`) — Started at
  `2026-05-19T08:00:00.500Z`, completed Successful at
  `2026-05-19T08:00:08.105Z`. The sibling's Running window
  (`[08:00:00.500, 08:00:08.105]`) fully contains the failing job's
  open attempt at `08:00:01.7xx`.
- Both jobs target the same process and the same workbook path.
- Trigger `HourlySalesA` (key `t1111111-...`): cron `0 */30 * * * ?`,
  process `ExcelDailyImport`.
- Trigger `HourlySalesB` (key `t2222222-...`): cron `0 */30 * * * ?`,
  process `ExcelDailyImport`. Identical schedule. Every fire produces
  overlapping job windows.

### Activity-package (Excel)
- Failing activity: `Read Range` inside `Use Excel File` scope on
  `sales-2026-05.xlsx`.
- The error is the .NET `IOException` for an exclusive-lock collision,
  not a UiPath-specific BusinessRuleException. Acquisition failed
  before any sheet or range parsing — sheet name and range are
  irrelevant to this failure.

### Cross-check — what this is NOT
- Not a user-Excel-UI-open (host is `MOCK-HOST`, unattended, no
  human-owned `EXCEL.EXE`).
- Not an orphan from a prior job (no prior faulted job; workflow
  source has no `ContinueOnError` on the scope).
- Not a network-share lock (workbook path is local `C:\Robot\Data\`,
  not UNC).
- Not an AV/EDR transient hold (failures are persistent on every
  overlap, not intermittent).

---

**Recommended Fix (Resolution):**

Serialize the process so two job firings of `ExcelDailyImport` cannot
run at the same time. Pick one:

1. **Single-performer queue.** Replace the time-based triggers with a
   queue, configure the queue with `1` performer, and have a dispatcher
   process enqueue one queue item per hour. The Robot processes items
   sequentially; the second item waits until the first completes and
   releases the workbook.
2. **Per-workbook lock asset.** Add an Orchestrator asset
   `lock-sales-2026-05` (text or boolean). At job start, acquire it
   (with retry); at job end (Finally), release it. The second job
   waits — or fails fast — until the first releases.
3. **Stagger the triggers.** Change `HourlySalesB` to fire on
   `15 */30 * * * ?` (offset by 15 minutes from `HourlySalesA`) so the
   Running windows do not overlap. Only viable if a single job's
   runtime stays well under 15 minutes.

Verify by re-running with the chosen serialization in place and
confirming `or jobs list --folder-key f0011111-... --process-name
ExcelDailyImport` no longer shows overlapping `StartTime`/`EndTime`
windows.

**Prevention:** For any workbook that more than one Orchestrator
process may touch, do not rely on Excel's own lock to coordinate —
the IOException surface is too noisy. Default to per-workbook lock
assets or single-performer queues at design time. Audit trigger
schedules against process runtime when adding a new trigger.
