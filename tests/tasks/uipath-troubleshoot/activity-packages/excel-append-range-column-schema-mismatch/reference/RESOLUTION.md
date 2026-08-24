# Final Resolution

---

**Root Cause:** The workflow's `Append Range` activity received a
`DataTable` (`dtNewHires`) whose 4 columns are ordered
`[EmployeeId, HireDate, FullName, Department]`, but the target
sheet `Employees` already has a header row with the columns in a
different order: `[FullName, EmployeeId, Department, HireDate]`.
Append Range writes by **position**, NOT by header name — so source
column 0 (`EmployeeId`, numeric Int64) was marshalled into target
column A (the existing `FullName` text column). Excel COM rejected
the cell write with `System.Runtime.InteropServices.COMException
(0x800A03EC): Application-defined or object-defined error.`

The source DataTable and the target sheet have the SAME 4 columns
by name — but in different orders. The workflow author likely
assumed Append Range would map columns by header name (a reasonable
mental model that the activity doesn't implement).

**What went wrong:** Failing job
`ff222222-cccc-dddd-eeee-ffffaaaabbbb` started at
`2026-05-28T08:00:01.300Z`. The HR sub-workflow returned a 12-row,
4-column DataTable. The `Use Excel File: employees.xlsx` scope
opened the workbook via the COM provider. The `Append Range: new
hires` activity read the target sheet's existing header row, found
4 columns in a different order than the source, located the last
data row (847), computed the append target starting at row 848,
and began marshalling row 1. The first cell write — source
`EmployeeId` (Int64 value 10847) into target column A
(`FullName`, stored type Text) — was rejected by Excel COM with
the standard 0x800A03EC HRESULT.

**Why:** Excel COM's `Range.set_Value` enforces the destination
cell's stored type when the source value's runtime type would
require a coercion Excel doesn't perform implicitly (e.g., writing
an Int64 into a column whose cells use the Text storage type with
text-formatted values). Even if the type coercion would succeed
(Int64 → string representation), the activity's column-alignment
validator surfaces the order mismatch as a hard rejection in
package versions that include the mismatch detection.

Append Range's by-position semantics are documented but
counterintuitive — the visual presence of header names in both
the source DataTable and the target sheet creates a false
expectation of by-name mapping. The fix is to align the source's
column order to match the target's BEFORE the append, OR
restructure both ends to agree on a canonical order.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelHRProcess` (key `ff222222-...`) — Faulted at
  `2026-05-28T08:00:03.812Z`.
- Folder: `HROps` (key `f0099999-3333-4444-5555-666677778888`).
- Host: `MOCK-HOST`. Robot user: `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `System.Runtime.InteropServices.COMException (0x800A03EC):
  Application-defined or object-defined error.` with stack trace
  through
  `Microsoft.Office.Interop.Excel.Range.set_Value(Object, Object)`,
  `UiPath.Excel.Activities.Business.AppendRangeX.WriteRowBlock(Range, DataRow)`,
  and `AppendRangeX.OnExecute(NativeActivityContext)`.
- Faulting activity: `AppendRange_1` (`Append Range: new hires`)
  at `Main.xaml`.

### Workflow source (decisive)
- `Main.xaml`:
  - `Invoke FetchNewHires.xaml` → `dtNewHires`. The sub-workflow
    returns a DataTable with column order
    `[EmployeeId, HireDate, FullName, Department]`.
  - `Use Excel File: employees.xlsx` (Modern scope, COM provider).
  - `<uix:ExcelAppendRange SheetName="Employees" DataTable="[dtNewHires]" AddHeaders="False" />`
  - There is NO column-reordering / `DataTable.DefaultView.ToTable`
    transformation between the sub-workflow's return and the
    Append Range activity.

### Job logs (decisive)
- `Invoke: FetchNewHires.xaml — returned dtNewHires with 12 rows, 4 columns (EmployeeId, HireDate, FullName, Department)`
- `Use Excel File: employees.xlsx — workbook opened (COM provider)`
- `Append Range: new hires — target sheet 'Employees' header row read: ['FullName', 'EmployeeId', 'Department', 'HireDate'] (4 columns)`
- `Append Range: new hires — last data row in target sheet 'Employees': row 847. Append target starts at row 848.`
- `Append Range: new hires — marshalling row 1 of 12 to Excel COM (A848:D848): writing source column 0 'EmployeeId' (value=10847, type=Int64) to target column A 'FullName' (stored type: Text)`
- `Append Range: new hires — COM Range.set_Value rejected cell A848: source column order ['EmployeeId', 'HireDate', 'FullName', 'Department'] vs target header order ['FullName', 'EmployeeId', 'Department', 'HireDate'] — Append writes by POSITION, columns don't align`
- `Append Range: new hires — System.Runtime.InteropServices.COMException (0x800A03EC): Application-defined or object-defined error.`

The decisive log line names BOTH column orders side-by-side and
explicitly states "Append writes by POSITION, columns don't align."
The cell-level rejection at A848 (source col 0 EmployeeId → target
col A FullName) ties the type mismatch to the position mismatch.

### Cross-check — what this is NOT
- Not branch 1 (activity variant mismatch): the activity is wrapped
  in `Use Excel File` properly; scope validation passed and the
  activity dispatched to the provider.
- Not branch 2 (sheet name mismatch / extension): the target sheet
  `Employees` exists and the header row was read successfully —
  it's the COLUMN ALIGNMENT WITHIN that sheet that mismatches, not
  the sheet identity.
- Not branch 3 (workbook locked / read-only): the workbook opened
  cleanly per the logs.
- Not branch 4 (uninitialized DataTable): `dtNewHires` is
  populated (12 rows, 4 columns).
- Not branch 6 (hidden rows in target): the target's append region
  starts at row 848 (immediately after row 847); the BusinessException
  is the COM rejection, not the package v2.8.5+ hidden-rows
  BusinessException.

---

**Recommended Fix (Resolution):**

### Primary fix — reorder the source DataTable to match the target

Insert a column-reorder step between the HR sub-workflow's return
and the Append Range activity. Use `DataTable.DefaultView.ToTable`
to materialize a new DataTable with the column order matching the
target's existing header:

1. Open `Main.xaml`.
2. Insert an `Assign` activity between `Invoke: FetchNewHires.xaml`
   and the `Use Excel File` scope.
3. Configure:
   - **To**: `dtNewHires`
   - **Value**: `dtNewHires.DefaultView.ToTable(False, "FullName", "EmployeeId", "Department", "HireDate")`
4. The column-name list MUST match the target sheet's header order
   exactly.
5. Save and re-run.

After the reorder, the Append Range writes EmployeeId values (col 1
in the new order) into target column B (the target's EmployeeId
column), which has the right stored type — the COM rejection
disappears.

### Alternative — restructure the source sub-workflow

If the source-side column order is misaligned at the producer
(`FetchNewHires.xaml`) rather than introduced downstream, fix it at
the source. Edit `FetchNewHires.xaml` to populate its output
DataTable in the canonical order matching the target sheet's
header. This is the "fix it at the producer" approach — better for
the long term but requires changes to the sub-workflow.

### Alternative — restructure the target sheet

If the source's column order represents a newer, preferred
convention (e.g., the HR system was updated to expose columns in
the canonical order), update the target workbook's existing header
row to match the source. This requires migrating the existing 847
rows of data to the new column order — a one-time data migration,
not a per-run fix.

### Anti-pattern (do NOT use)

Do NOT add a `Try Catch` around the Append Range that catches
`COMException` and continues. Excel COM may have appended SOME
rows before rejecting (depending on where the order mismatch
surfaces first in the marshalling sequence) — the catch turns
the partial write into a "success" with stale or wrongly-ordered
data in the target. Downstream consumers reading the workbook
then see misaligned columns with no error logged. Use Try-Catch
only with a real recovery path (e.g., retry after a column
reorder, log a structured alert to ops).

### Prevention

- When designing an Append Range workflow, document the target
  sheet's column contract (column names AND their canonical
  positions). Apply a column-reorder step on every source
  DataTable before the append.
- Don't assume Append Range maps columns by header name — it
  maps by position. This is documented but counterintuitive;
  treat the by-position semantics as an explicit constraint in
  the workflow design.
- Log `DataTable.Columns.Count` and the names of the source
  DataTable's columns immediately before the append. Pair with
  a `Get Workbook Sheets` or similar pre-check that reads the
  target's header — having both columnar shapes in the logs
  makes branch 5 self-diagnosing.
- For workflows where the source's column order can drift over
  time (e.g., an external API that occasionally adds columns):
  use a name-based DataTable transformation step that projects
  ONLY the target's expected columns in the target's order. New
  source columns get dropped silently; missing source columns
  produce a clear error you can handle.
- Consider switching to `Write Range` against a computed target
  region (with explicit column mapping) for workflows where
  Append Range's by-position semantics are a frequent source of
  defects. Write Range is more verbose but eliminates the
  by-position trap.
