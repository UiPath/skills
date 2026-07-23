# Final Resolution

---

**Root Cause:** The `ExcelWriteCellProcess` workflow's `Write Cell`
activity is nested inside a `For Each Row` loop iterating a
DataTable read from the workbook. Each iteration writes a single
cell — over a 247-iteration run, that's 247 separate
`Range.Value = ...` COM calls plus the implicit
open-save-close churn that `Use Excel File` performs around each
write. Excel COM accumulates COM-object leaks, the file-lock
churn races with itself, and after enough iterations the
activity faults with the canonical
`UiPath.Excel.BusinessException: The data you want to write has
a wrong format, or Excel is busy.`

The "or Excel is busy" clause is misleading on the formula-syntax
branch (branch 2 — nothing is busy) but ACCURATE here: the Excel
instance is destabilized from the open/save/close thrash, and
the activity cannot acquire a clean Range object to write into.

The partial-success pattern (247 iterations OK, then failure)
plus the restart non-determinism (a different N each run) are
the decisive fingerprints of branch 3 — a deterministic data
problem (branch 2) would fail on iteration 1 every time.

**What went wrong:** Failing job
`33cc3333-2222-3333-4444-555566667777` started at
`2026-05-20T08:00:01.300Z`. The `Use Excel File` scope opened
`sales-2026-05.xlsx`. The `Read Range` activity read 312 rows
into a DataTable. The `For Each Row` loop began iterating; for
each row, the workflow assigned a computed value
(`row("Status") = ComputeStatus(row)`), then called `Write Cell`
to write that value to the corresponding `Status` column cell.
Iterations 1 through 247 succeeded (`Write Cell: row 1 written
to E2`, `... row 2 written to E3`, …). On iteration 248 the
activity faulted with the BusinessException.

**Why:** Excel COM is not designed for the cell-by-cell write
pattern that `Write Cell` inside a loop creates. Each invocation
acquires the workbook's `Range` COM object, calls `Range.Value
= ...`, optionally saves, and releases. Over many iterations:

- COM Runtime Callable Wrapper (RCW) garbage collection lags
  behind allocation, leaking interface pointers.
- The file lock is acquired and released N times — file-system
  caching layers race with each other.
- Excel COM's internal state machine (calculation engine,
  formula dependency graph, autofilter state) accumulates
  cruft.

The threshold (N) varies between runs because it depends on
host memory pressure, GC timing, and other non-deterministic
factors. A restart that processes 300 rows successfully on one
run and 150 rows on the next is a textbook fingerprint of
state-corruption-induced failure rather than data-induced
failure.

The fix is structural: collapse the N file open/close cycles
into 2 by reading the workbook into a DataTable once, mutating
rows in memory inside the loop, and writing the entire table
back via Write Range after the loop. This eliminates the COM
thrash entirely.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelWriteCellProcess` (key `33cc3333-...`) --
  Faulted at `2026-05-20T08:04:18.412Z`.
- Folder: `ExcelWrites` (key
  `f0022222-2222-3333-4444-555566667777`).
- Host: `MOCK-HOST`. Robot user: `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `UiPath.Excel.BusinessException: The data you want to write
  has a wrong format, or Excel is busy.`
- Faulting activity: `WriteCell_1` (`Write Cell: row N
  status`) at `Main.xaml`, iteration 248 of 312.

### Job logs (decisive)
- `Use Excel File: sales-2026-05.xlsx -- workbook opened`
- `Read Range: A1:F313 -- 312 rows read`
- `For Each Row -- iteration 1 of 312`
- `Write Cell: row 1 status -- row 1 written to E2`
- `For Each Row -- iteration 2 of 312`
- `Write Cell: row 2 status -- row 2 written to E3`
- ... (245 similar log lines)
- `For Each Row -- iteration 247 of 312`
- `Write Cell: row 247 status -- row 247 written to E248`
- `For Each Row -- iteration 248 of 312`
- `Write Cell: row 248 status -- UiPath.Excel.BusinessException:
  The data you want to write has a wrong format, or Excel is
  busy.`

The 247 successful iterations preceding the failure are the
smoking gun. Branch 2 (formula syntax) would fail on iteration
1 since the malformed input is identical every time.

### Workflow source (decisive)
- `Main.xaml`:
  - `<uix:UseExcelFile WorkbookPath="C:\Robot\Data\sales-2026-05.xlsx" ...>`
  - Inside its Body:
    - `<uix:ReadRange Range="A1:F313" SheetName="Sales"
      Result="[Rows]" .../>` --- reads 312 rows.
    - `<ui:ForEachRow DataTable="[Rows]" ...>` --- **loop**.
      - Inside the loop body:
        - `<ui:Assign To="[row(&quot;Status&quot;)]"
          Value="[ComputeStatus(row)]"/>` --- computes status.
        - `<uix:WriteCell Range="[&quot;E&quot; &amp;
          (CInt(row(&quot;RowIndex&quot;).ToString) +
          1).ToString]" SheetName="Sales"
          Value="[row(&quot;Status&quot;).ToString]"
          .../>` --- **Write Cell inside the loop**.
- The `Write Cell` inside `For Each Row` is the structural smoking
  gun for branch 3.

### Restart non-determinism (decisive)
- The user noted "restarting the job lets it process a different
  number of rows before failing again." This is incompatible with
  branch 2 (which would fail at the same point every time) and
  diagnostic for state-corruption-induced failure (branch 3).

### Cross-check -- what this is NOT
- Not branch 1 (file locked / scope conflict): the error class
  is `BusinessException`, not `IOException`. The workbook
  opened successfully and 247 writes succeeded.
- Not branch 2 (formula syntax): the partial-success pattern
  rules this out — formula errors are deterministic. Also, the
  written Value is a computed string (`row("Status").ToString`),
  not a formula.
- Not branch 4 (sheet not found): 247 writes to the same
  sheet succeeded before the failure; the sheet clearly exists.
- Not branch 5 (protected sheet): 247 writes succeeded; the
  sheet is not protected.
- Not branch 6 (invalid cell reference): 247 cell references
  (`E2`, `E3`, ..., `E248`) resolved correctly; iteration 248's
  cell reference (`E249`) is no more invalid than the others.

---

**Recommended Fix (Resolution):**

### Primary fix -- bulk Read Range → DataTable → Write Range

Replace the cell-by-cell write pattern with bulk operations
that collapse N file open/close cycles into 2:

1. The `Read Range` already populates a `DataTable` (call it
   `Rows`). Keep it.
2. Inside the `For Each Row` loop, REMOVE the `Write Cell`
   activity. Keep the `Assign` that computes `row("Status") =
   ComputeStatus(row)` — this mutates the row in memory only.
3. After the `For Each Row` loop exits, add a single `Write
   Range` activity that writes the mutated `Rows` DataTable
   back to the workbook in one call:
   ```
   Write Range:
     Range = "A1"
     SheetName = "Sales"
     DataTable = [Rows]
     AddHeaders = True
   ```
4. Re-run. The workflow now opens the workbook once, reads
   once, computes in memory, writes once, and closes. Linear
   I/O instead of quadratic.

### Why this works

- Excel COM's `Range.Value = <2D-array>` for a contiguous range
  is a single COM call that internally batches all cell
  assignments. The `Write Range` activity uses this path.
- No per-iteration file save / lock release / lock acquire
  cycle.
- Excel COM RCW lifecycle stays bounded: one allocation, one
  release.

### What NOT to do

- **Do NOT add a `Retry Scope` around the `Write Cell`.** The
  underlying Excel COM state is corrupt; retrying produces the
  same failure (often immediately, sometimes after a few more
  iterations as background GC catches up). Retries are for
  transient failures, not state corruption.
- **Do NOT add `Delay` activities inside the loop.** Slowing
  down the thrash does not fix the COM-object leak. It just
  makes the same failure happen later in wall-clock time. The
  problem is the pattern, not the speed.
- **Do NOT pivot to the branch 2 fix** (replace semicolons with
  commas in formulas). The `Value` here is a computed string,
  not a formula. Branch 2 does not apply.
- **Do NOT increase `task_timeout` / `max_turns` and hope the
  job finishes.** The failure mode is non-deterministic — a
  job that succeeds with a longer timeout one day will fail the
  next.

### Prevention

- For any cell-by-cell write pattern, prefer Read Range →
  in-memory DataTable mutation → Write Range. Reserve `Write
  Cell` for single targeted writes (a header, a status flag, a
  timestamp) — not for bulk data.
- If a per-cell pattern is unavoidable (the writes are
  interleaved with reads that depend on intermediate computed
  values), batch them: collect the writes into a
  `List<(string Cell, object Value)>` during the loop, then
  drain the list outside the loop where COM thrash is bounded.
- Avoid `Save Workbook` inside any loop. Modern `Use Excel File`
  controls save semantics through the scope's `AutoSave`
  property; setting it to False and saving once at the end of
  the workflow eliminates per-iteration disk I/O.
- For workbooks that legitimately need many independent writes
  (~thousands), consider switching to OpenXML-based libraries
  (e.g., a custom invoke-code activity using ClosedXML or
  EPPlus) that bypass Excel COM entirely. UiPath's Excel
  activities are optimized for human-scale workbook
  interactions, not high-throughput data writes.
