# Final Resolution

---

**Root Cause:** The workflow has two sequential Modern `Use Excel
File` cards (against different workbooks: `sales-q1.xlsm` and
`sales-q2.xlsm`) with `ReadFormatting=True` — a COM-forcing
property that pushes the Modern surface from its OpenXML default
into Excel COM fallback. There is NO outer `Excel Process Scope`
wrapping the two cards. When the first card's body completed,
its scope-owned-lifecycle policy terminated the EXCEL.EXE process
(PID 8472) on scope exit. The second card then attempted to attach
to the same Excel COM apartment to satisfy its own COM fallback —
but PID 8472 no longer exists. The COM apartment proxy returns
`0x80010108 RPC_E_DISCONNECTED` ("The object invoked has
disconnected from its clients."), which the activity surfaces
as-is.

**What went wrong:** Failing job
`aa222222-cccc-dddd-eeee-ffffaaaabbbb` started at
`2026-05-30T09:00:01.300Z`. `UseExcelFile_1` (sales-q1.xlsm)
launched EXCEL.EXE PID 8472 (ReadFormatting=True forced COM),
the inner Read Range returned 1247 rows successfully, the body
completed, the scope exited and terminated PID 8472. Two
seconds later `UseExcelFile_2` (sales-q2.xlsm) tried to reuse
the Excel COM apartment from the previous scope — but the
apartment was gone with the process. The card retried for ~3.5s
before surfacing the RPC_E_DISCONNECTED COMException.

**Why:** Modern `Use Excel File` cards are designed to own the
EXCEL.EXE process lifecycle PER scope when they're forced into
COM mode and there's no outer governor. The first card's
scope-end terminates the process so it doesn't leak; the second
card has to launch its own. But the second card's COM acquisition
path includes an apartment-reuse optimization that tries to
attach to the previous process before launching a new one — and
that path fails immediately when the previous process is gone.

The canonical fix is the `Excel Process Scope` activity: an outer
container that governs EXCEL.EXE lifecycle ACROSS multiple inner
`Use Excel File` cards. With it, both cards share one EXCEL.EXE
that lives for the duration of the outer scope. Without it,
each card opens/closes EXCEL.EXE independently and the race is
inherent.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelMultiReportProcess` (key `aa222222-...`) —
  Faulted at `2026-05-30T09:00:08.412Z`.
- Folder: `QuarterlyReports` (key `f00ccccc-3333-4444-5555-666677778888`).
- Host: `MOCK-HOST`. Robot user: `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `System.Runtime.InteropServices.COMException (0x80010108): The
  object invoked has disconnected from its clients.
  (RPC_E_DISCONNECTED)` with stack trace through
  `UiPath.Excel.Activities.Business.UseExcelFile.AcquireWorkbook(String)`
  and `UseExcelFile.OnExecute(NativeActivityContext)`. Inner
  detail names the dead PID 8472.
- Faulting activity: `UseExcelFile_2` (`Use Excel File:
  sales-q2.xlsm`) at `Main.xaml`.

### Workflow source (decisive)
- `Main.xaml` outer Sequence:
  - `Log Message` "starting multi-report"
  - `<uix:UseExcelFile WorkbookPath="C:\Robot\Data\sales-q1.xlsm" ReadFormatting="True" ...>` (UseExcelFile_1, COM-forcing)
  - `<uix:UseExcelFile WorkbookPath="C:\Robot\Data\sales-q2.xlsm" ReadFormatting="True" ...>` (UseExcelFile_2, COM-forcing)
  - `Log Message` "reports loaded"
- **There is NO `<uix:ExcelProcessScope>` wrapping the two
  `UseExcelFile` cards.** This is the structural defect.
- Both cards set `ReadFormatting="True"` — the COM-forcing
  property that turns these otherwise-OpenXML scopes into COM
  scopes, surfacing the lifecycle issue.

### Job logs (decisive)
- `Use Excel File: sales-q1.xlsm — ReadFormatting=True forces COM fallback (OpenXML provider declined). Launching new EXCEL.EXE process (PID 8472).`
- `Read Range: Q1 sales — returned 1247 rows. Body of UseExcelFile_1 complete.`
- `Use Excel File: sales-q1.xlsm — scope exiting. No outer Excel Process Scope detected: terminating EXCEL.EXE PID 8472 per scope-owned-lifecycle policy.`
- `Use Excel File: sales-q2.xlsm — ReadFormatting=True forces COM fallback. Attempting to reuse Excel COM apartment from previous scope (PID 8472).`
- `Use Excel File: sales-q2.xlsm — COM apartment for PID 8472 is unreachable (process terminated). HRESULT 0x80010108 RPC_E_DISCONNECTED.`
- `Use Excel File: sales-q2.xlsm — System.Runtime.InteropServices.COMException (0x80010108): The object invoked has disconnected from its clients. (RPC_E_DISCONNECTED)`

The chain is decisive: scope 1 launches PID 8472, completes, exits
the scope (which terminates PID 8472 — the scope-owned-lifecycle
log line explicitly names "No outer Excel Process Scope detected"),
scope 2 tries to reuse the gone apartment and hits RPC_E_DISCONNECTED.

### Cross-check — what this is NOT
- Not branch 1 (Excel not installed): UseExcelFile_1 succeeded
  in launching EXCEL.EXE PID 8472 — Excel IS installed. The
  failure is the apartment race AFTER the first scope teardown.
- Not branch 2 (empty / illegal WorkbookPath): both paths
  resolved cleanly, both scopes opened their respective
  workbooks.
- Not branch 4 (child outside scope): both Read Range activities
  are correctly nested inside their respective UseExcelFile cards.
- Not branch 5 (sensitivity label): no `BusinessException` /
  `COMException` referencing sensitivity / Purview / AIP.

---

**Recommended Fix (Resolution):**

### Primary fix — wrap both cards in an Excel Process Scope

Insert an `Excel Process Scope` (Modern, outermost) that contains
both `Use Excel File` cards. The Process Scope governs the
EXCEL.EXE lifecycle across the inner scopes — both cards share
one EXCEL.EXE process for the duration of the Process Scope.

1. Open `Main.xaml`.
2. Drag an `Excel Process Scope` activity into the outer Sequence
   (toolbox: App Integration → Excel → Excel Process Scope).
3. Move both `Use Excel File` cards (UseExcelFile_1 and
   UseExcelFile_2) INSIDE the Excel Process Scope's body.
4. Save and re-run.

The structural shape becomes:
```
Sequence
├── Log: starting multi-report
├── Excel Process Scope
│   └── Body
│       ├── Use Excel File: sales-q1.xlsm
│       │   └── Read Range: Q1 sales
│       └── Use Excel File: sales-q2.xlsm
│           └── Read Range: Q2 sales
└── Log: reports loaded
```

With the Process Scope wrapping both cards, the second card sees
the same EXCEL.EXE process the first card used, no
termination-between-scopes happens, and the RPC_E_DISCONNECTED
race disappears.

### Alternative — remove the COM-forcing property

If the workflow doesn't actually NEED Excel formatting interaction
(the `ReadFormatting=True` property was set "just in case"),
remove it from both cards. Without COM-forcing, the cards default
to OpenXML — no EXCEL.EXE process at all, no apartment race
possible.

1. On both UseExcelFile cards, change `ReadFormatting` from
   `True` to `False` (or omit the property).
2. Save and re-run.

Trade-off: OpenXML doesn't support every Excel feature COM does
(rich formatting, certain formula behaviors, macros). If the
workflow genuinely needs those, this option doesn't apply.

### Alternative — restructure into a single Use Excel File

If the two workbooks could be consolidated into one file (e.g.,
two sheets `Q1` and `Q2` in `sales-yearly.xlsm`), a single
`Use Excel File` reads both — no cross-scope race possible.
This is a workbook-side change, not a workflow-side change, and
may not fit every business context.

### Anti-pattern (do NOT use)

Do NOT add a `Delay` activity between the two `Use Excel File`
cards as a "fix." The Delay sometimes works because the OS-level
process cleanup happens to complete within the delay window — but
the underlying race is still there. On a slow host, on a host
under load, or after a Windows update that changes process cleanup
timing, the Delay-based fix breaks intermittently. The Process
Scope wrap is the structural solution that eliminates the race
regardless of timing.

This is the playbook's anti-pattern #1.

### Prevention

- For workflows with two or more sequential `Use Excel File`
  cards (or any combination of Modern + Classic Excel scopes
  in sequence), default to wrapping them in an `Excel Process
  Scope`. The Process Scope is cheap (no per-iteration cost
  when there's only one inner card) and prevents the cross-scope
  race when the workflow grows.
- Audit `ReadFormatting`, `Edit Password`, `Visible: True`, and
  certain `AutoSave` combinations on Modern `Use Excel File`
  cards. These properties force COM fallback. If the workflow
  doesn't NEED Excel COM features, remove them — OpenXML is
  faster, more reliable, and avoids the apartment / process
  surfaces entirely.
- For workflows that iterate over many workbooks in a loop
  (`For Each Workbook`), wrap the loop in an Excel Process
  Scope. Per-iteration scope teardown plus a fresh launch is
  expensive AND race-prone; the Process Scope amortizes the
  EXCEL.EXE lifecycle across the loop.
- Document COM-forcing property usage in workflow comments. A
  comment near each `ReadFormatting=True` saying "this workflow
  needs to read cell formatting because <reason>" prevents
  future contributors from removing the property accidentally
  AND signals to deployment owners that Excel must be installed
  on the Robot host.
