# Final Resolution

---

**Root Cause:** The `ExcelWriteCellProcess` workflow contains a
Modern `Use Excel File` scope on `C:\Robot\Data\sales-2026-05.xlsx`
that holds the workbook open through its body. Inside the scope's
body, the workflow invokes a Classic Workbook `Write Cell`
activity with its OWN `WorkbookPath` property pointing at the
same file. The Classic Workbook surface accesses the file's raw
bytes directly (it does not delegate to the surrounding scope)
and refuses to write while another process holds the file — and
the surrounding Modern scope IS another process from the OS's
perspective.

The user explicitly ruled out external lockers: "no human had
it open, and there are no other jobs running against it." That
exclusion is the second decisive signal — combined with the
workflow source showing the dual-scope pattern, the diagnosis
is the Classic/Modern scope conflict, not the external-locker
variant of the file-locked playbook.

**What went wrong:** Failing job
`11aa1111-2222-3333-4444-555566667777` started at
`2026-05-20T08:00:01.300Z`. The `Use Excel File` scope opened
`sales-2026-05.xlsx` successfully (logged at
`08:00:01.510`). Inside the scope's body, the workflow then
invoked a Classic Workbook `Write Cell` (display name
`Write Cell: status=Done`) configured with `WorkbookPath` =
`C:\Robot\Data\sales-2026-05.xlsx`, `Range` = `D1`, `Value` =
`"Done"`. The Classic Workbook activity tried to open the file
for writing and the OS refused because the Modern scope already
had it open.

**Why:** The two Excel surfaces in `UiPath.Excel.Activities` own
files by different mechanisms:

- **Modern `Use Excel File`** opens the workbook once at scope
  entry and routes nested activities (`Read Range`, modern
  `Write Cell`, `Read Cell`, etc.) through the same open handle.
  Nested activities cooperate — they share the scope's file
  handle.
- **Classic Workbook activities** (e.g., `Write Cell` configured
  with a `WorkbookPath` property and no surrounding scope) open
  the file independently for the duration of the activity. They
  do NOT cooperate with a surrounding Modern scope — the
  surrounding scope's open handle is invisible to them, and the
  Classic activity's own open attempt collides with it.

A Classic Workbook activity inside a Modern scope is therefore
two independent opens on the same file inside the same job —
the OS sees a write-write conflict and surfaces `IOException`.

The error wording is identical to a genuine external locker
(orphan `EXCEL.EXE`, user editing, network-share lock) — the
.NET IO message does not name the locking process. Distinguishing
the scope-conflict variant from the external-locker variant
requires reading the workflow source.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelWriteCellProcess` (key `11aa1111-...`) --
  Faulted at `2026-05-20T08:00:02.812Z`.
- Folder: `ExcelWrites` (key
  `f0022222-2222-3333-4444-555566667777`).
- Host: `MOCK-HOST`. Robot user: `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `System.IO.IOException: The process cannot access the file
  'C:\Robot\Data\sales-2026-05.xlsx' because it is being used by
  another process.`
- Faulting activity: `WriteCell_1` (Classic Workbook
  `Write Cell`) at `Main.xaml`.

### Job logs (decisive when combined with workflow source)
- `Use Excel File: sales-2026-05.xlsx -- workbook opened`
- `Use Excel File: sales-2026-05.xlsx -- read range completed (10 rows)`
- `Write Cell: status=Done -- opening workbook (Classic Workbook surface)`
- `Write Cell: status=Done -- System.IO.IOException: The process
  cannot access the file 'C:\Robot\Data\sales-2026-05.xlsx'
  because it is being used by another process.`

The "opening workbook (Classic Workbook surface)" trace line is
the smoking gun — the Classic Workbook activity is opening the
file independently rather than reusing the surrounding scope's
handle.

### Workflow source (decisive)
- `Main.xaml`:
  - `<uix:UseExcelFile WorkbookPath="C:\Robot\Data\sales-2026-05.xlsx" .../>`
    --- Modern scope opens the file.
  - INSIDE its `Body`:
    - `<uix:ReadRange Range="A1:B10" .../>` --- Modern activity,
      cooperates with the scope (fine).
    - `<uix:WriteCell DisplayName="Write Cell: status=Done"
      WorkbookPath="C:\Robot\Data\sales-2026-05.xlsx" Range="D1"
      Value="Done" .../>` --- **Classic Workbook activity with
      its own `WorkbookPath`**, opens the file independently and
      collides with the scope.
- The presence of a Classic Workbook activity (identified by its
  own `WorkbookPath` property) INSIDE a Modern scope is the
  structural smoking gun.

### User exclusion (decisive)
- "No human had it open, and there are no other jobs running
  against it." Explicitly rules out branches 1 (user editing),
  2 (orphan EXCEL.EXE), 3 (network-share lock), 4 (concurrent
  Robot jobs), 5 (AV/EDR), and 6 (other user session) of the
  `read-range-file-locked.md` playbook.

### Cross-check -- what this is NOT
- Not `read-range-file-locked.md` external-locker variant: the
  user has explicitly ruled out external lockers, and the
  workflow source shows the dual-scope pattern.
- Not branch 2 (formula syntax) or branch 3 (loop thrash): the
  error class is `IOException`, not
  `UiPath.Excel.BusinessException`. The Excel COM layer is not
  involved in this failure -- the file-system layer is.
- Not branch 4 (sheet not found): the error fires before any
  sheet resolution; the activity could not open the file at
  all.
- Not branch 5 (protected sheet): the error class would be
  `COMException`, not `IOException`.
- Not branch 6 (invalid cell reference): same -- the error
  would fire later, after file open.

---

**Recommended Fix (Resolution):**

### Primary fix -- nest Modern Write Cell inside the existing scope

The cleanest fix replaces the Classic Workbook activity with a
Modern `Write Cell` that participates in the surrounding scope:

1. Open `Main.xaml` in Studio (or edit XAML directly).
2. Replace the Classic Workbook `<uix:WriteCell ...
   WorkbookPath="...">` element with a Modern `Write Cell`
   activity that takes the workbook reference from the
   surrounding scope (no `WorkbookPath` property -- the scope
   owns the file).
3. Re-run the job to verify.

### Alternative -- move the Classic activity OUT of the scope

If for any reason the Classic Workbook surface is required
(e.g., the workflow depends on a Classic-only property), move
the Classic activity outside the Modern scope's `Body`:

1. Drag the Classic `Write Cell` out of the `Use Excel File`
   block so it runs AFTER the scope releases the file.
2. Re-run.

### What NOT to do

- **Do NOT add a `Kill Process` activity for `EXCEL` before the
  Write Cell.** There is no `EXCEL.EXE` to kill -- the locker is
  UiPath's own scope, not an external Excel process. A blanket
  `Kill Process` masks the underlying scope-management bug and
  terminates other legitimate Excel work on the host.
- **Do NOT pivot to the `read-range-file-locked.md`
  investigation chain** (orphan check, network share, AV
  scanner). The user has explicitly excluded those and the
  workflow source identifies the cause unambiguously.
- **Do NOT add a `Retry Scope`** around the Write Cell. Retrying
  the same Classic-inside-Modern pattern produces the same
  IOException every time.

### Prevention

- Pick one Excel surface per workflow and stay on it. New
  workflows: prefer Modern `Use Excel File` + nested Modern
  activities. Existing workflows: do not introduce Classic
  Workbook activities into a Modern scope's body.
- Treat the presence of both a Modern scope and a Classic
  Workbook activity (recognizable by an explicit `WorkbookPath`
  property on the activity itself) targeting the same file as a
  code smell. Catch it at PR review.
- For workflows that legitimately need both surfaces (rare),
  serialize: Modern scope completes first (its `Body` exits),
  THEN Classic activities run on the file. Two scopes on the
  same file at the same time always conflict.
