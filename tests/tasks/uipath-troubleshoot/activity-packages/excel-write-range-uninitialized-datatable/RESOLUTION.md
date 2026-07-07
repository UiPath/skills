# Final Resolution

---

**Root Cause:** The workflow's `Write Range` activity receives the
`dtSource` variable, but `dtSource` was never assigned a value during
this run because the preceding `Read Range` is nested inside an `If`
activity whose condition (`File.Exists("C:\Robot\Data\customer-source.xlsx")`)
evaluated to `False`. The source workbook was missing on the host
filesystem, so the entire Then-branch — including the Read Range that
populates `dtSource` — was skipped. The `Write Range` activity then
tried to dispatch with a `Nothing` DataTable argument and threw
`System.NullReferenceException` at its argument-resolution step,
before any provider call was made.

**What went wrong:** Failing job
`ee111111-cccc-dddd-eeee-ffffaaaabbbb` started at
`2026-05-24T08:00:01.300Z`. The `If` activity evaluated
`File.Exists("C:\Robot\Data\customer-source.xlsx")` to `False` and
skipped its Then-branch (no error logged, just a skipped branch).
The export-side `Use Excel File` then opened `customer-export.xlsx`
cleanly. The `Write Range: export customers` activity attempted to
resolve its `DataTable` argument `dtSource`, found it was `Nothing`
(no assignment had ever run for it in this execution path), and
threw the canonical NRE.

**Why:** A `DataTable` variable declared but never assigned defaults
to `Nothing` in VB.NET. The `Write Range` activity's argument
resolver dereferences the variable to read `.Rows` and `.Columns`
for its provider call; that dereference is what throws the NRE.
The activity has no nullness guard on its `DataTable` input — it
treats a `Nothing` argument as a programmer error rather than a
recoverable empty case. (The `Ignore empty source` property, when
the activity supports it, also doesn't help here — it only changes
behavior for an initialized 0-row table, not a `Nothing` variable.)

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelExportProcess` (key `ee111111-...`) — Faulted
  at `2026-05-24T08:00:02.812Z`.
- Folder: `DataExports` (key `f0055555-3333-4444-5555-666677778888`).
- Host: `MOCK-HOST`. Robot user: `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `System.NullReferenceException: Object reference not set to an instance of an object.`
  with stack trace through
  `UiPath.Excel.Activities.Business.WriteRangeX.ResolveSourceTable(NativeActivityContext)`
  and `WriteRangeX.OnExecute(NativeActivityContext)`.
- Faulting activity: `WriteRange_1` (`Write Range: export customers`)
  at `Main.xaml`.

### Workflow source (decisive)
- `Main.xaml`:
  - `<Variable x:TypeArguments="sd:DataTable" Name="dtSource" />` —
    declared with no default, defaults to `Nothing`.
  - `<If Condition="[File.Exists(&quot;C:\Robot\Data\customer-source.xlsx&quot;)]">`
    — only Then-branch present, no Else. The Then-branch wraps the
    `Use Excel File: customer-source.xlsx` + `Read Range` that
    would have populated `dtSource`.
  - `<uix:ExcelWriteRange DataTable="[dtSource]" ... />` — at the
    outer scope, AFTER the If, regardless of which branch ran.

### Job logs (decisive)
- `If source workbook exists — condition: File.Exists("C:\Robot\Data\customer-source.xlsx") evaluated to False (file not found on host filesystem). Then-branch skipped.`
- `Use Excel File: customer-export.xlsx — workbook opened (OpenXML provider)`
- `Write Range: export customers — resolving DataTable argument 'dtSource'`
- `Write Range: export customers — DataTable argument 'dtSource' resolved to Nothing (no assignment found in execution path)`
- `Write Range: export customers — System.NullReferenceException: Object reference not set to an instance of an object.`

The chain `If condition False → Then-branch skipped → dtSource
never assigned → Write Range sees Nothing → NRE` is the smoking
gun. The exception happens on the activity itself, not inside any
Excel COM / OpenXML call — the activity throws before it ever
touches the workbook.

### Cross-check — what this is NOT
- Not branch 2 (workbook locked / read-only): the export workbook
  opened cleanly per the logs; no `IOException`, no
  "cannot access the file" COMException.
- Not branch 3 (empty source + ExcludeHeaders=False): the source
  is `Nothing`, not an initialized 0-row DataTable. The
  BusinessException signature for empty-source is different
  ("Ignore empty source is ineffective" / "Failing on Empty Header").
- Not branch 4 (hidden rows / columns): the workbook's hidden state
  is irrelevant because the activity threw before any provider
  call. No `BusinessException` mentioning "hidden rows" was logged.
- Not branch 5 (out-of-memory / COMException): no
  `OutOfMemoryException`, no `0x800A03EC`. The activity never
  reached the data-marshaling layer.

---

**Recommended Fix (Resolution):**

### Primary fix — initialize the variable at declaration

The cheapest, most defensive change: initialize `dtSource` to an
empty `DataTable()` so the Write Range never sees `Nothing`, even
when the upstream branch is skipped.

1. Open `Main.xaml`.
2. Edit the `dtSource` variable declaration to set its default
   value to `New System.Data.DataTable()`.
3. Save and re-run.

With an initialized empty `dtSource`, the failure shifts to branch 3
(empty source + ExcludeHeaders=False). Handle that with the next fix
below — they're complementary.

### Primary fix (companion) — guard the Write Range

Wrap the Write Range in an `If` activity with condition
`dtSource IsNot Nothing AndAlso dtSource.Rows.Count > 0`. In the
Then-branch, perform the write. In the Else-branch, log a warning
that the source was missing or empty.

This explicitly encodes the "nothing to write" semantics rather than
relying on the activity to handle either the `Nothing` case
(branch 1) or the 0-row case (branch 3).

### Alternative — fail fast when the source is missing

If the workflow's contract is "the source workbook MUST exist," make
the missing-file case an explicit failure rather than a silent
branch-skip:

1. Replace the `If File.Exists(...)` with an unconditional
   `Use Excel File: customer-source.xlsx`. The Use Excel File
   activity will throw a `FileNotFoundException` if the workbook is
   missing, which is a clearer error than the downstream NRE.
2. Or: add an explicit `Throw` activity in the `Else`-branch of the
   `If` saying "Source workbook not found at <path>".

### Alternative — move the Write Range inside the If

If the export is only meaningful when the source exists, move the
entire export sequence (the second `Use Excel File` + `Write Range`)
inside the `If`'s Then-branch. The Then-branch becomes the entire
export pipeline; the Else-branch is a no-op or logs the
"nothing to export" case.

### Prevention

- Initialize all `DataTable` variables at declaration (default to
  `New DataTable()`). Treat `Nothing` as never-valid for a DataTable
  in Write Range scope.
- Log `DataTable.Rows.Count` and `DataTable.Columns.Count`
  immediately before every Write Range. Two log lines are cheap
  insurance against branches 1 and 3 — and turn a silent NRE into
  a self-diagnosing trace.
- Don't rely on `Ignore empty source` — it only handles the
  `Nothing` case, not the 0-row case. Both need to be guarded
  separately.
- For workflows that conditionally produce data: explicitly handle
  the "no data" path with an `Else` branch or an early-return
  pattern, rather than letting an unset variable propagate to a
  downstream activity that wasn't designed for it.
- For variables whose source is an upstream `Read Range`: verify
  the upstream activity actually executes in every execution path
  that reaches the Write Range. Skipped branches are the most
  common cause of branch 1.
