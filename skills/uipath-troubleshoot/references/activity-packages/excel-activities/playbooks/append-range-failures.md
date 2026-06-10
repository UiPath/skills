---
confidence: medium
---

# Append Range Failures

## Context

A `UiPath.Excel.Activities` `Append Range` activity appends a `DataTable`'s rows to the bottom of an existing sheet, after the last row containing data. The package exposes the operation through three surfaces with materially different runtime semantics:

1. **Classic `Append Range` inside `Excel Application Scope`** — opens the workbook through Excel COM; requires Excel installed on the host. Inherits the scope's open workbook reference.
2. **Modern `Append Range` (`AppendRangeX`) inside `Use Excel File`** — opens the workbook through the OpenXML provider (default) or falls back to Excel COM when scope properties force it.
3. **Classic `Append Range Workbook`** — the standalone Workbook surface that reads / writes the file's raw bytes directly without an enclosing scope and without requiring Excel installed.

Failures originate at one of six surfaces: activity-variant mismatch (wrong surface for the deployment), sheet-name or file-extension resolution, file acquisition (workbook locked), source-table integrity (null DataTable), source-vs-target schema alignment (columns don't match the existing sheet), or target-region structural state (hidden rows on the append target under package v2.8.5+).

What this looks like — Append Range faults surface as one of these signatures:

- `UiPath.Excel.BusinessException` referencing "must be placed inside an `Excel Application Scope`" or "must be placed inside a `Use Excel File`" — the activity variant in the workflow doesn't match its surrounding container (or has no container). Branch 1.
- `System.Runtime.InteropServices.COMException (0x800A03EC): Application-defined or object-defined error` — Excel COM rejected the operation. For Append Range, two distinct underlying causes share this HRESULT: branch 2 (sheet name mismatch or unsupported file extension passed to a COM-only call) and branch 5 (the cell write itself rejected due to a schema mismatch). Distinguish by the surrounding evidence (logs, target inspection).
- `System.IO.IOException: The process cannot access the file '<path>' because it is being used by another process.` — file held by another process or by a stale scope. Branch 3.
- `System.NullReferenceException: Object reference not set to an instance of an object.` — the configured `DataTable` argument is `Nothing`. Branch 4.
- `UiPath.Excel.BusinessException` mentioning "hidden rows" or "hidden columns" — the calculated append region intersects hidden rows on the target sheet (package v2.8.5+ only). Branch 6.

What can cause it (cause-branches — pick the right one from evidence):

1. **Activity variant mismatch (Append Range vs Append Range Workbook vs AppendRangeX)** — three surfaces with the same display name but different acquisition models. The classic `Append Range` activity dropped outside an `Excel Application Scope` throws a `BusinessException` at runtime because it has no workbook context. The Modern `Append Range` (`AppendRangeX`) outside a `Use Excel File` throws the equivalent. The standalone `Append Range Workbook` works independently and does NOT require a scope — but it accesses the file via direct bytes, so it can't coexist with an outer scope that already holds the workbook. Mixing surfaces against the same path in one workflow self-deadlocks on the file lock (collapses to branch 3's scope-conflict variant).
2. **Sheet name mismatch or invalid file extension** — the configured `SheetName` doesn't match any sheet in the workbook (typo, OpenXML case-sensitivity, sheet renamed upstream, leading/trailing whitespace), OR the workbook path uses an extension Excel COM doesn't recognize for write (`.xls` without the older Excel format support installed, `.xlsm` against an OpenXML-only call). Both surface with the generic `0x800A03EC` HRESULT or a more specific `BusinessException: The sheet with the name '<x>' does not exist` depending on package version. Cross-cuts the read-range sheet-not-found surface — the diagnostic is identical.
3. **Workbook locked or opened read-only** — same fault family as the read-range / write-range / delete-range file-locked surface: a different process holds the file (user-opened Excel UI, orphan `EXCEL.EXE` from a prior job, AV scanner, network-share lock from a different host), the file is read-only at the OS layer (NTFS ACL, `Mark as Final`, Protected View), OR the workflow mixes the Workbook surface with a Modern/Classic scope against the same path (the scope owns the file; the standalone Workbook activity refuses to acquire it).
4. **Uninitialized / null DataTable** — the source `DataTable` argument is `Nothing`. Causes: variable declared but never assigned (missing `Build Data Table` / `Read Range` step); preceding step skipped on a conditional branch; conditional output from `Filter DataTable` against an empty source that returned `Nothing` instead of an empty DataTable; variable-name typo so the activity reads the wrong scope's variable.
5. **Column schema mismatch (source DataTable vs target sheet)** — Append Range expects the source `DataTable`'s columns to align with the existing target sheet's header row. Common failure modes: the source has more columns than the target (extra columns spill into never-defined positions); the source has fewer columns (the activity may write into the wrong starting column, depending on `AddHeaders` and how the activity computes the append-start cell); column-type mismatches (e.g., source numeric column → target text column with stored-as-text values causes Excel to reject the write); column-order mismatches (Append writes by position, NOT by header name — so swapping two columns in the source produces a structurally-valid but semantically-corrupted append). Surfaces as `COMException 0x800A03EC` from `Range.set_Value`, OR a `BusinessException` referencing column count, OR a silent semantic corruption (no error, wrong column gets the wrong data — same pattern as branch 5 of delete-range / branch 5 of filter misalignment).
6. **Hidden rows in the target append region (package v2.8.5+)** — the workbook's target sheet has rows hidden where the append would land (the row immediately after the last visible data row, OR hidden rows between the last data row and a re-emerging data block). Pre-2.8.5 versions silently wrote into the hidden cells; 2.8.5+ throws an explicit `BusinessException` flagging the hidden range so the workflow author catches the data-shape risk. Common trigger: an AutoFilter applied to the target sheet that hides rows including or following the last-data row position.

What to look for:

- **The exception class and message** — first signal. `BusinessException` referencing missing scope → branch 1. `0x800A03EC` / `BusinessException` about sheet → branch 2 (or branch 5 if the sheet exists but columns mismatch). `IOException` / "cannot access the file" → branch 3. `NullReferenceException` → branch 4. `BusinessException` mentioning column count or wrong-type cell rejection → branch 5. `BusinessException` mentioning "hidden rows" → branch 6.
- **Workflow source** — which `Append Range` surface (Classic scoped / Modern scoped / Workbook standalone), the configured `DataTable` argument, `SheetName`, `AddHeaders`, the workbook path (including the extension), and the parent container.
- **The DataTable's source and shape** — what activity produced the source (`Build Data Table`, `Read Range`, `Generate Data Table`, etc.), how many columns it has, what column types and headers it carries. Required to confirm or rule out branches 4 and 5.
- **Target sheet's existing structure** — header row content (matters for branch 5's column-alignment check), hidden rows (branch 6), AutoFilter state, the last row containing data (branch 6 / branch 5).
- **Package version** — `UiPath.Excel.Activities` version from `project.json`. Branch 6 is version-gated at 2.8.5; pre-2.8.5 produces silent corruption with no exception.
- **Workbook extension** — `.xlsx`, `.xlsm`, `.xls`, `.xlsb`. The Modern scope's OpenXML provider supports `.xlsx` / `.xlsm` cleanly; `.xls` (legacy binary) requires COM. Branch 2's extension-mismatch variant lives here.

## Investigation

Go in this order — cheaper checks first.

1. **Capture the exact error, activity surface, and configuration.** From `uip or jobs get <job-key> --output json` → `Info`: exception class, full message, HRESULT (if a COMException), inner exception. From workflow source: the Append Range surface (Classic scoped / Modern scoped / Workbook standalone), parent container, configured `SheetName`, `AddHeaders`, the source DataTable variable, and the workbook path. From job logs (`uip or jobs logs <key>`): the activity's Trace lines, plus any `Log Message` lines capturing the DataTable shape before the activity.

2. **Branch the diagnostic on the exception signature.**
   - `BusinessException: ... must be placed inside an Excel Application Scope` / `... inside a Use Excel File` → branch 1; go to step 3.
   - `BusinessException: The sheet with the name '<x>' does not exist` → branch 2; pivot to the read-range sheet-not-found playbook for the full chain (see [`../summary.md`](../summary.md)).
   - `IOException` / `COMException` with "cannot access the file" / "used by another process" → branch 3; pivot to the read-range file-locked playbook (see [`../summary.md`](../summary.md)).
   - `NullReferenceException` → branch 4; go to step 4.
   - `COMException 0x800A03EC` without explicit sheet-name or hidden-rows language → branches 2 (extension / sheet) or 5 (column schema); go to step 5.
   - `BusinessException` mentioning "hidden rows" / "hidden columns" → branch 6; go to step 6.

3. **Confirm branch 1 (activity variant mismatch).** Inspect the workflow source. Three sub-cases:
   - The activity is **classic `Append Range`** (not the `Workbook` variant) and there is NO surrounding `Excel Application Scope`. Fix is structural: either wrap it in a scope OR switch to the standalone `Append Range Workbook` activity.
   - The activity is **Modern `Append Range` (`AppendRangeX`)** and there is NO surrounding `Use Excel File`. Same fix family: wrap in Modern scope OR switch surface.
   - The activity is **`Append Range Workbook`** (standalone) but the workflow ALSO has an `Excel Application Scope` / `Use Excel File` open against the same path elsewhere — that scope holds the file, the standalone Workbook surface can't acquire it. This is the scope-conflict variant of branch 3 in disguise; resolve by replacing the standalone Workbook activity with a scoped one nested inside the existing scope, OR remove the scope and use only the Workbook surface throughout.

4. **Confirm branch 4 (uninitialized DataTable).** Trace the `DataTable` argument's variable backward in the workflow source. Find the most recent assignment / output binding. If it's an upstream `Read Range`, did that activity succeed in this run (check job logs)? If it's `Build Data Table`, is the activity actually on the execution path? If the variable was declared in an inner scope, has it gone out of scope by the time Append Range runs? Add a `Log Message Level=Info Message=$"src rows={dt.Rows.Count}, cols={dt.Columns.Count}"` immediately before the activity and rerun — if that line throws NRE, the variable is null. The diagnostic chain is identical to Write Range's branch 1; the same fixes apply.

5. **Distinguish branch 2 (sheet/extension) from branch 5 (column schema) when both surface as `0x800A03EC`.** Both branches share the same generic Excel HRESULT and can produce the same `Range.set_Value` stack frame. Differentiate with these checks:
   - **Sheet existence**: open the workbook in Excel (or read its sheet list via `Get Workbook Sheets`). If the configured `SheetName` does not match any sheet → branch 2 (sheet name). If the sheet exists → continue.
   - **Extension support for the provider**: read the workbook path's extension. The Modern OpenXML provider supports `.xlsx` and `.xlsm`. The Workbook surface supports `.xlsx`, `.xlsm`, `.xlsb`, `.xls` natively without Excel. The Classic Excel scope supports whatever the installed Excel version supports. A `.xls` (legacy binary) against a Modern scope's OpenXML provider can throw 0x800A03EC; switching to COM mode (or replacing with a Workbook surface) fixes it.
   - **Source vs. target column alignment**: open the target workbook in Excel. Inspect the target sheet's existing header row and the column data types of the last-data row. Compare to the source DataTable's columns (count, names, types). If the source has more columns than the target, OR a source column's type doesn't match the target's stored type at that position, OR the source column order differs from the target's header order → branch 5 (schema mismatch).

6. **Confirm branch 6 (hidden rows in target append region).** Two checks:
   - **Package version**: read `UiPath.Excel.Activities` from `project.json`. If < 2.8.5, branch 6 doesn't exist in this version — recheck the exception text against other branches. If ≥ 2.8.5, continue.
   - **Target sheet hidden state**: open the workbook in Excel before running the workflow. Locate the last row that contains data on the target sheet. Inspect the rows immediately after (where the append would land) and any rows between data blocks. Look for: AutoFilter funnel icons (active filter hiding rows); manually hidden rows (gap in row numbers); grouped rows collapsed. Any of these in the append target triggers branch 6.

The root cause is **which of the six surfaces** the failure maps to. A confirmed finding names the activity surface (Classic scoped / Modern scoped / Workbook standalone), the source DataTable's runtime shape, the target sheet's structure, and the matching exception signature.

## Resolution

Map the branch identified in Investigation to the fix:

- **Branch 1 — Activity variant mismatch:**
  - **Classic `Append Range` outside `Excel Application Scope`**: wrap it in `Excel Application Scope` with the workbook path configured on the scope. If the Robot host doesn't have Excel installed (common for headless / unattended Robots), switch to the standalone `Append Range Workbook` activity instead — it doesn't require Excel and works on the file's raw bytes.
  - **Modern `AppendRangeX` outside `Use Excel File`**: wrap it in `Use Excel File` with the workbook configured on the scope.
  - **`Append Range Workbook` alongside another scope on the same path**: replace the standalone Workbook activity with a scoped one nested inside the existing scope. Don't mix surfaces against the same file in one workflow — the scope and the Workbook surface acquire the file by different mechanisms and self-deadlock.
  - Prevention: pick one Excel surface (Classic, Modern, or Workbook) per workbook path in a workflow, and stick to it. Mixing surfaces is the leading cause of self-inflicted file-acquisition failures.

- **Branch 2 — Sheet name mismatch or invalid file extension:**
  - **Sheet mismatch**: apply the resolution from the read-range sheet-not-found playbook (see [`../summary.md`](../summary.md) for navigation). Correct the configured `SheetName` to match the workbook's actual sheet name verbatim — including case under OpenXML, whitespace, and Unicode normalization. Validate dynamic expressions with `Get Workbook Sheets` at workflow start before the Append Range runs.
  - **Extension mismatch**: confirm the workbook extension is compatible with the activity surface. `.xls` files require Excel COM (Classic scope or Workbook with appropriate installation); `.xlsb` requires the Workbook surface. If the Modern scope is forcing OpenXML on a non-OpenXML extension, either change the workbook to `.xlsx` (re-save in Excel) or switch to a surface that supports the extension natively.

- **Branch 3 — Workbook locked or read-only:**
  - Apply the resolution from the read-range file-locked playbook (see [`../summary.md`](../summary.md) for navigation). The append side and the read side share the same fault surface — the file is held by another process, the lock is at the OS layer, or the workflow mixes scope surfaces against the same path.
  - For `Append Range Workbook` against a path also referenced by an outer scope: pick one surface (see branch 1's prevention rule).

- **Branch 4 — Uninitialized / null DataTable:**
  - Initialize the variable at declaration (`New System.Data.DataTable()` as the default). With an initialized empty DataTable, the failure shifts to whichever case actually applies (likely a no-op append, or branch 5 if columns don't align).
  - Guard the Append Range with `If dt IsNot Nothing AndAlso dt.Rows.Count > 0 Then` and skip on the empty case.
  - Trace the upstream populating activity to ensure it actually executes in every execution path that reaches Append Range. The diagnostic chain is identical to Write Range's branch 1.

- **Branch 5 — Column schema mismatch:**
  - **Align columns by position** (the activity writes by position, not by header name):
    - Confirm the source DataTable's columns match the target sheet's column order, count, and types.
    - For mismatched ORDER: reorder the source DataTable's columns via `dt = dt.DefaultView.ToTable(False, "Col1", "Col2", "Col3")` (the second argument is the column-name list in target-sheet order).
    - For extra source columns: select only the target's columns via the same `ToTable(False, ...)` call.
    - For missing source columns: add the missing columns to the source DataTable (`dt.Columns.Add("MissingCol")`) so the append fills them — even if the values are empty/null.
  - **Align column types**:
    - Check the target sheet's actual storage type per column (not just the header label). A column showing "1234" rendered right-aligned is numeric; "1234" left-aligned with a green corner triangle is stored as text. Source values must match.
    - Use `Convert.ToString(...)`, `Convert.ToDecimal(...)`, etc. on the DataTable's row population step to coerce types before the append.
  - **Disambiguate AddHeaders behavior**: if the target sheet already has a header row and the source DataTable also carries headers, set `AddHeaders=False` on the activity so the source headers aren't duplicated as a data row in the target.
  - Prevention: when designing an Append Range workflow, document the target's column contract (column names, positions, types) and apply it as a transformation step on the source DataTable before the append. Don't rely on the source's natural column order to match the target's.

- **Branch 6 — Hidden rows in target append region (package v2.8.5+):**
  - Remove hidden rows from the target append zone before the Append Range:
    - **Active AutoFilter**: insert a `Remove Data Filter` (Modern) or `Filter Range Action=Remove` (Classic) immediately before Append Range. After the append, re-apply the filter if downstream consumers depend on it.
    - **Manually hidden rows**: unhide programmatically (`Worksheet.Rows.Hidden = False` via COM) or in Excel before deployment.
    - **Grouped rows collapsed**: expand the group before the append.
  - If the hidden state is intentional and the append region must not be reorganized, route the append to a different sheet whose layout is robot-controlled, then have a downstream step (separate workflow) consolidate the data into the user-facing sheet.
  - Downgrading the package to pre-2.8.5 to silence the error is the playbook's anti-pattern — it reintroduces the silent-data-loss bug that the explicit error was added to catch.

## Anti-patterns (what NOT to do)

Common advice for Append Range failures contains workarounds that hide bugs rather than fix them. The agent should NOT recommend any of these as a primary resolution.

- **"Add a `Delay` activity before Append Range."** A Delay is a workaround for a race condition or initialization issue that the workflow author has not diagnosed. For Append Range, the most common temptation is to add a delay after opening the workbook (masking branch 3) or after a preceding write operation (masking a timing dependency that the workflow should encode explicitly). The Delay works intermittently and hides the real cause. Fix the underlying timing (kill orphan EXCEL.EXE for branch 3; sequence activities correctly so the dependency is explicit).

- **"Wrap Append Range in a bare Try Catch and continue on error."** A bare Try-Catch that catches `Exception` / `BusinessException` / `COMException` and only logs without re-throwing turns Append Range failures into silent partials — Excel COM may have appended SOME rows before rejecting at a problem row, and the catch turns the partial write into a "success" with stale / missing data in the target. Downstream consumers reading the target then operate on a corrupted append. Use Try-Catch only with a real recovery path: retry with cleaned data (branches 4 and 5), notify on persistent file-lock (branch 3), or re-throw a domain-specific exception.

- **"Switch to Append Range Workbook to silence the scope error."** The standalone Workbook surface IS a legitimate alternative when the deployment host doesn't have Excel installed. But switching to it WITHOUT understanding why the original scoped activity was failing can mask real bugs — e.g., a workflow that needed COM features (formula recalculation, conditional formatting interaction) will silently produce wrong data with the Workbook surface even though the failure goes away. Pick the surface based on the deployment requirements (does the workflow need Excel features? is Excel installed on the host?), not based on which one stops throwing.

- **"Downgrade `UiPath.Excel.Activities` to pre-2.8.5 to silence the hidden-rows error."** Branch 6's explicit error was added BECAUSE pre-2.8.5 versions silently appended over hidden rows, causing data loss that workflow authors only discovered weeks later when human users unhid rows. Downgrading reintroduces the bug. The correct fix is to handle the hidden-rows case explicitly (remove the filter, unhide, or route to a different sheet).

## Prevention (cross-branch)

- Pick one Excel surface per workbook path per workflow. Classic scoped, Modern scoped, OR Workbook standalone — don't mix. Mixing causes branch 1's scope-conflict variant of branch 3.
- Document the target sheet's column contract (order, types, header row presence) and apply it as an explicit transformation step on the source DataTable before Append Range. Branch 5's column-mismatch failures are far cheaper to diagnose when the alignment is explicit.
- Initialize all `DataTable` variables at declaration (default to `New DataTable()`). Combined with an `If dt.Rows.Count > 0` guard, this handles both branch 4 (null) and the empty-case no-op cleanly.
- Log `DataTable.Rows.Count` and `DataTable.Columns.Count` immediately before every Append Range. The two-line log makes branches 4 and 5 self-diagnosing.
- For workflows on a sheet that humans also edit: insert a `Remove Data Filter` (Modern) or equivalent Classic step before every Append Range. AutoFilter state is invisible to the workflow author at design time but very visible to the activity under v2.8.5+ (branch 6).
- For Robot hosts WITHOUT Excel installed: prefer the `Append Range Workbook` surface package-wide. The Classic / Modern scopes will fail at acquisition; the Workbook surface won't.
- For workbooks accessed by multiple workflows: serialize Excel access (single-performer queues, host-level locks) to prevent branch 3 collisions between concurrent jobs.

## Related

- Other Excel Activities failure fingerprints (read-side and write-side cross-cuts — file-locked, sheet-not-found, protected-sheet) are separate playbooks; see [`../summary.md`](../summary.md) for navigation. Branches 2 (sheet) and 3 (file lock) inherit the diagnostic chains from those playbooks.
- [`./delete-range-failures.md`](./delete-range-failures.md) — sibling range-mutation playbook. The hidden-rows / AutoFilter pattern (branch 6 here / branch 5 there) is structurally identical in both directions; the fix for one applies to the other.
- [`./execute-macro-failures.md`](./execute-macro-failures.md) — sibling playbook for `Execute Macro` failures. Workflows that combine Append Range with VBA post-processing share the scope-container and file-acquisition surfaces.
- [`../overview.md`](../overview.md) — package overview, including the scope-container model and the OpenXML-vs-COM provider distinction relevant to branches 1 and 2.
- For headless workflows where the append target is best expressed in code rather than DataTable-to-sheet, consider migrating to the cloud surface via `o365-activities/` (Microsoft Graph API). That surface has different memory and concurrency semantics and no Excel COM dependency, avoiding branches 1, 3, and 6 entirely.
