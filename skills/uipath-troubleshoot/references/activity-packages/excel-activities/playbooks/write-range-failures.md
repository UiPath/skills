---
confidence: medium
---

# Write Range Failures

## Context

A `UiPath.Excel.Activities` `Write Range` activity (Classic `WriteRange` inside `Excel Application Scope` / standalone Workbook surface, or Modern `WriteRangeX` inside `Use Excel File`) writes a `DataTable` to a worksheet starting at a configured cell. Failures originate at one of five surfaces: source-table integrity (the `DataTable` variable is null), file acquisition (workbook locked / read-only), source-shape edge cases (header-only DataTable with `ExcludeHeaders=False`), target-sheet structure (hidden rows / columns inside the write boundary as of package v2.8.5+), or data volume / content (oversized batches, formula-prefix characters interpreted as broken formulas).

What this looks like — Write Range faults surface as one of these signatures:

- `System.NullReferenceException: Object reference not set to an instance of an object` — the configured `DataTable` argument is `Nothing` / `null`. Branch 1.
- `System.IO.IOException: The process cannot access the file '<path>' because it is being used by another process.` — file held by another process or by a stale UiPath scope. Branch 2.
- `UiPath.Excel.BusinessException` (wording varies — typically "The Excel Activity option 'Ignore empty source' is ineffective" or "Failing on Empty Header") — the source `DataTable` has 0 rows AND `ExcludeHeaders` is False. Branch 3.
- Explicit error (package v2.8.5+) referencing hidden rows / columns within the target write region — `UiPath.Excel.BusinessException` mentioning "hidden rows or columns" or similar. Branch 4.
- `System.OutOfMemoryException`, `System.Runtime.InteropServices.COMException`, or `UiPath.Excel.BusinessException: The data you want to write has a wrong format, or Excel is busy.` — branch 5 (oversized batches or formula-prefix data).

What can cause it (cause-branches — pick the right one from evidence):

1. **Uninitialized / null DataTable** — the source `DataTable` variable passed to the activity is `Nothing`. Causes: variable declared but never assigned (missing `Build Data Table` / `Read Range` step earlier); preceding `Read Range` ran against a missing sheet and returned `Nothing` instead of an empty DataTable; conditional branch skipped the assignment; variable name typo so the activity reads the wrong scope's variable. Symptom is the canonical NRE on the activity, NOT inside Excel — the activity throws before any COM / OpenXML call.
2. **Workbook locked or opened read-only** — same fault family as the read-range / delete-range / write-cell file-locked surface: a different process holds the file (user-opened Excel UI, orphan `EXCEL.EXE` from a prior job, AV scanner, a different host's lock on a network share), OR the file is read-only at the OS layer (NTFS ACL, `Mark as Final`, Protected View on a downloaded copy, Modern `Use Excel File` scope with `ReadOnly=True`).
3. **Empty source DataTable + `ExcludeHeaders=False`** — the source DataTable has 0 rows (only column definitions, no data). With `ExcludeHeaders=False` (default), the activity tries to write the header row + 0 data rows; some surfaces / package versions surface this as a BusinessException rather than a no-op. The note in the activity's documentation that "`Ignore empty source` excludes the empty case" is misleading — `Ignore empty source` only applies when the DataTable variable itself is `Nothing`, not when it's an initialized table with 0 rows. Workflow authors hit this when a preceding `Filter DataTable` removed every row, leaving the schema but no content.
4. **Hidden rows / columns in the target write range (package v2.8.5+)** — the workbook's target sheet has rows or columns hidden inside the rectangle the `DataTable` would write into (manual hide, AutoFilter, or grouping). Pre-2.8.5 versions silently wrote into the hidden cells and the user saw "missing" data; 2.8.5+ throws an explicit `BusinessException` flagging the hidden ranges so the workflow author catches the data-loss risk before it ships. Common trigger: a sheet shared with a human user who applied a filter before the job ran.
5. **Out-of-memory / COM exceptions on volume or formula-prefix data** — two distinct sub-causes that share signatures:
   - **Oversized batches**: writing a multi-hundred-thousand-row `DataTable` in one call exhausts Excel COM's per-call buffer (or .NET managed memory under heavy COM marshaling). Surfaces as `OutOfMemoryException` or `COMException` with a generic Excel HRESULT (`0x800A03EC`, `0x8001010A`).
   - **Formula-prefix data**: cell values starting with `=`, `+`, `-`, or `@` are interpreted by Excel as formulas. When the literal text isn't a valid formula (e.g., `=Smith, John` for a name with a leading equals), Excel rejects the cell with `Application-defined or object-defined error`. Same signature as the volume case, different root.

What to look for:

- **The exception class and message** — first signal. `NullReferenceException` → branch 1. `IOException` / "cannot access the file" → branch 2. `BusinessException` mentioning "empty source" / "Ignore empty source" / "header" → branch 3. `BusinessException` mentioning "hidden rows" / "hidden columns" → branch 4. `OutOfMemoryException` or `COMException` with a generic Excel HRESULT → branch 5 (large or formula-prefix).
- **Workflow source** — which `Write Range` surface (Classic Workbook / Classic scope / Modern), the configured `DataTable` argument (literal variable name vs. an expression), the configured `SheetName` / `Range` / `ExcludeHeaders` / `AddHeaders`, and the parent container (`Excel Application Scope`, `Use Excel File`, or unwrapped Classic Workbook).
- **The DataTable's source** — what activity produced the `DataTable` variable (`Build Data Table`, `Read Range`, `Generate Data Table from Text`, `Filter Data Table`, a coded assignment, etc.). Branch 1 traces back to whichever step was expected to populate it.
- **Package version** — `UiPath.Excel.Activities` version from `project.json`. The hidden-rows behavior (branch 4) is version-dependent: pre-2.8.5 silently writes; 2.8.5+ throws.
- **Target sheet state** — visible AutoFilter (funnel icons on header row), manually hidden rows / columns, grouped rows / columns collapsed, freeze panes intersecting the write range. Relevant for branch 4.
- **`DataTable.Rows.Count` immediately before the activity** — gives branch 1 vs. branch 3 vs. valid-but-failed distinction. A `Log Message` capturing the row count + the `DataTable.Columns.Count` is the cheapest pre-write check.

## Investigation

Go in this order — cheaper checks first.

1. **Capture the exact error, activity, and configuration.** From `uip or jobs get <job-key> --output json` → `Info`: exception class, full message, HRESULT (if COMException), inner exception. From workflow source: the `Write Range` surface (Classic Workbook / Classic scope / Modern), the configured `DataTable` argument (variable name or expression), `SheetName`, `Range`, `ExcludeHeaders`, `AddHeaders`, and the parent container. From job logs (`uip or jobs logs <key>`): the activity's Trace lines around the failure, plus any `Log Message` lines that captured the `DataTable.Rows.Count` immediately before.

2. **Branch the diagnostic on the exception signature.**
   - `NullReferenceException` → branch 1; go to step 3.
   - `IOException` / `COMException` with "cannot access the file" / "used by another process" / "read-only" → branch 2; pivot to the read-range file-locked playbook for the full chain (see [`../summary.md`](../summary.md) for navigation).
   - `BusinessException` mentioning "Ignore empty source" / "empty source" / "header" → branch 3; go to step 4.
   - `BusinessException` mentioning "hidden rows" / "hidden columns" / "hidden range" → branch 4; go to step 5.
   - `OutOfMemoryException` or `COMException` with generic Excel HRESULT (`0x800A03EC`, `0x8001010A`) → branch 5; go to step 6.
   - `BusinessException: The sheet with the name '<name>' does not exist` → cross-cutting sheet-name mismatch; pivot to the read-range sheet-not-found playbook (see [`../summary.md`](../summary.md)). The diagnostic is identical to the read-side version.
   - `COMException` with "protected" / "read-only" / `0x800A03EC` near `Worksheet.Protect` → cross-cutting protected-sheet surface; pivot to the write-cell playbook's branch 5 (see [`../summary.md`](../summary.md)).

3. **Confirm branch 1 (uninitialized DataTable).** Inspect the workflow source. Trace the `DataTable` argument's variable backward:
   - Find the most recent assignment / output binding for that variable in scope. If it's an `Assign`, did the expression resolve? If it's a `Read Range` output, did that activity succeed in this run? If it's a `Build Data Table` output, is the activity actually upstream of Write Range in the execution path (not in an `Else` branch that was skipped)?
   - Add a `Log Message Level=Info Message=$"dt rows={dt.Rows.Count}, cols={dt.Columns.Count}"` immediately before the Write Range and rerun. If the log line throws NRE itself, the variable is null. If it logs `rows=0 cols=N`, branch 1 is ruled out and the failure is branch 3.
   - Check the variable scope: a `DataTable` declared in an inner scope (`Try` body, `If` then-branch) goes out of scope at the parent boundary; if Write Range is outside, it reads `Nothing`.
   - Check for variable-name typos: `dtCustomers` vs. `dtCustomer` — Studio doesn't always flag a misspelled reference if a same-named variable exists in an outer scope.

4. **Confirm branch 3 (empty source + ExcludeHeaders=False).** Check:
   - The `DataTable.Rows.Count` immediately before the activity is 0.
   - `ExcludeHeaders` is False (the default for many surfaces).
   - The DataTable was initialized (i.e., not branch 1) — confirmed if `DataTable.Columns.Count > 0`.
   - The preceding activity that should have populated rows actually ran and matched something. Common upstream cause: `Filter DataTable` with a predicate that matches no rows, or `Read Range` against a sheet that exists but has only a header row.
   - If `Range` is configured as a specific cell (e.g., `"A2"`) rather than empty / `"A1"`, the activity expects to write into existing data and the empty-source branch becomes more confusing because there's no header-row context.

5. **Confirm branch 4 (hidden rows / columns in target range).** Two independent checks:
   - **Package version**: open `project.json` and read `UiPath.Excel.Activities` version. If < 2.8.5, the explicit "hidden range" error does not exist in that version — the failure cannot be branch 4 by definition; recheck the exception text against the other branches.
   - **Target sheet state**: open the workbook in Excel before running the workflow. On the target sheet, look for: AutoFilter funnel icons on the header row (`Data → Filter` toggle); manually hidden rows (right-click row header → Unhide visible? gap in row numbers); manually hidden columns (gap in column letters); grouped rows / columns (left-margin or top-margin outline brackets); freeze panes. Any of these inside the rectangle defined by `(Range starting cell) + (DataTable shape)` triggers branch 4.
   - Reproduce manually: open the workbook in Excel, select the same target range, try to paste any value. If Excel rejects the paste with a "selection contains hidden cells" warning, the activity's BusinessException is the API-level surface of that same rejection.

6. **Confirm branch 5 (out-of-memory / COM exception).** Distinguish the two sub-causes:
   - **Volume sub-cause**: `DataTable.Rows.Count` is in the high thousands / hundreds of thousands at the time of write. The job logs may show progressive memory pressure earlier (cache warnings, GC pauses). Surfaces more often on COM-mode Modern scope or Classic surfaces (OpenXML is more memory-efficient).
   - **Formula-prefix sub-cause**: scan the DataTable's first column / first row of data for values starting with `=`, `+`, `-`, or `@`. Common offenders: names with a leading equals (`=Smith, John` from a copy-paste error), formulas in a column the user thought was plain text, accounting / debit values that begin with `-`, email handles starting with `@`. The activity will surface this as a `COMException` referencing "Application-defined or object-defined error" or "wrong format" — the same signature as the volume sub-cause but the cause is content, not size.
   - To distinguish without re-running: a `Log Message Level=Info Message=$"first cell of first row: '{dt.Rows(0)(0)}'"` immediately before Write Range exposes the value. If it starts with `=`, `+`, `-`, or `@`, branch 5 formula-prefix is the cause.

The root cause is **which of the five surfaces** the failure maps to. A confirmed finding names the surface (Classic / Modern), the resolved runtime state of the inputs (DataTable null vs. empty vs. populated, file-acquisition state, target sheet hidden state, data volume / first-row content), and the matching exception signature.

## Resolution

Map the branch identified in Investigation to the fix:

- **Branch 1 — Uninitialized / null DataTable:**
  - Trace the variable backward to its expected source and ensure that source actually executes. If the upstream is `Read Range`, confirm the sheet name and range resolve (rule out a silent miss). If the upstream is `Build Data Table`, ensure it sits on the execution path that reaches Write Range (not behind an `If` that the run skipped).
  - Initialize the variable at declaration: assign `dt = New System.Data.DataTable()` (or use `Build Data Table` at workflow start) so the variable is never `Nothing` even if the populating step is skipped. Write Range against a 0-row initialized DataTable becomes branch 3, not branch 1 — handle there.
  - Promote the variable's scope: if Write Range is at a higher scope than the assignment, move the variable declaration up to the common parent scope.
  - Fix variable-name typos: rename for clarity if a similar name exists in an outer scope (e.g., `dtCustomersFiltered` instead of reusing `dtCustomers` across nested scopes).
  - Prevention: prefer `Log Message Level=Info Message=$"dt rows={dt.Rows.Count}"` before every Write Range. The two extra log lines turn a silent NRE into a self-diagnosing trace.

- **Branch 2 — Workbook locked or read-only:**
  - Apply the resolution from the read-range file-locked playbook (see [`../summary.md`](../summary.md) for navigation). The write side (Write Range) and the read side share the same fault surface — the file is held by another process, the lock is at the OS layer, or the file is on a network share whose semantics differ from local disk.
  - For workbooks marked read-only via `Mark as Final` or arriving via Protected View: open the file as the Robot user, remove the `Mark as Final` flag (`File → Info → Mark as Final`), or `Unblock-File '<path>'` to lift the Mark-of-the-Web flag that triggers Protected View.
  - For Modern `Use Excel File` scopes: confirm `ReadOnly: False` on the scope. Default-True is a footgun on `Use Excel File` for workflows that include any Write activity.
  - For Classic Workbook `Write Range` (no enclosing scope) ALSO running alongside a Classic `Excel Application Scope` or Modern `Use Excel File` for the same path elsewhere in the workflow: replace the bare Classic Workbook Write Range with one nested inside the existing scope. Mixing surfaces against the same file is a self-inflicted lock — the scope owns the file via its mechanism, and the standalone Workbook activity refuses to acquire it.

- **Branch 3 — Empty source + `ExcludeHeaders=False`:**
  - Wrap Write Range in an `If` activity with condition `dt.Rows.Count > 0`. In the Then branch, perform the write. In the Else branch, log a warning or no-op. This is the cleanest fix because it explicitly encodes the "nothing to write" semantics rather than relying on the activity to handle it.
  - Set `ExcludeHeaders=True` if the workflow's intent is to write only data rows (no header in the workbook). With `ExcludeHeaders=True`, an empty DataTable is treated as a 0-row, 0-column write — usually a no-op rather than an error.
  - For workflows that aggregate filtered batches: validate the filter result earlier in the workflow. If `Filter DataTable` is the upstream cause, log the input vs. output row counts so the empty case is observable upstream rather than at the Write Range surface.
  - Note that `Ignore empty source` (when the activity / surface supports it) only handles the `Nothing` case (branch 1) — it does NOT handle an initialized DataTable with 0 rows. The two cases need to be handled separately, despite naming that suggests otherwise.

- **Branch 4 — Hidden rows / columns in target range (v2.8.5+):**
  - Remove hidden rows / columns from the target write region before the Write Range:
    - **Active AutoFilter**: insert a `Remove Data Filter` (Modern) or `Filter Range` with `Action: Remove` (Classic) targeting the same sheet, immediately before Write Range. After the write, re-apply the filter if downstream consumers depend on it.
    - **Manually hidden rows / columns**: select all rows / columns containing the write target, right-click, Unhide. For a robot-only sheet, automate this with a `Hidden = False` property write OR a pre-cleanup workflow step that calls `Worksheet.Unhide()` via COM.
    - **Grouped rows / columns collapsed**: expand the group (`Data → Ungroup`, or `Outline → Expand`) before the write. The Robot's session sees the collapsed state as hidden.
  - If the hidden state is intentional (e.g., a report uses hidden rows for archived records that should NOT be overwritten), restructure the target range so the write does not intersect the hidden region — write to a separate sheet or a non-overlapping range.
  - Downgrading the package to pre-2.8.5 silences the explicit error but reintroduces the silent-data-loss bug it was added to catch. Do not downgrade as a "fix"; the error is correctly flagging a real risk.

- **Branch 5 — Out-of-memory / COM exceptions:**
  - **Volume sub-cause**: chunk the write. Replace a single `Write Range` of `N` rows with a loop that writes batches of 5,000–20,000 rows each (tune to the workbook / host). Use `Append Range` for batches after the first, or a per-batch `Write Range` with a computed starting cell `"A" + ((batchIndex * batchSize) + 2).ToString()`. The 20K-row threshold is empirical — workbooks with many columns or rich types should use smaller batches.
  - Alternative for the volume sub-cause: switch to the OpenXML provider if you're on Classic / Modern COM. `Use Excel File` defaults to OpenXML when no COM-forcing property is set; OpenXML's memory footprint is much smaller for large data.
  - **Formula-prefix sub-cause**: pre-clean the data before the write. Two approaches:
    - **Escape the literal**: prepend an apostrophe (`'`) to each offending cell value via a `For Each Row` + cell update. Excel treats apostrophe-prefixed strings as literal text. The apostrophe is hidden in the rendered cell but stored.
    - **Pre-clean by type**: if the column should be text-only (names, IDs), enforce a `String` type on the DataTable column with `Convert.ToString(...).TrimStart("="c, "+"c, "-"c, "@"c)` to strip leading formula characters. Document the transformation in the workflow so consumers know the data has been sanitized.
  - For workflows that write user-supplied content into Excel (form input, scraped names, queue payloads): always apply the escape / pre-clean step. Do not assume input data is formula-safe.

## Anti-patterns (what NOT to do)

Common advice for Write Range failures contains workarounds that hide bugs rather than fix them. The agent should NOT recommend any of these as a primary resolution.

- **"Add a `Delay` activity before Write Range."** A `Delay` is a workaround for a race condition or initialization issue that the workflow author has not actually diagnosed. For Write Range, the most common temptation is to add a delay before the activity to "let Excel settle" after a preceding `Use Excel File` open, or to mask branch 2 (file lock) by waiting for a stuck process to release. The Delay works intermittently — long enough for the lock to release in the test environment but not in production. A reliable fix names the timing dependency: kill orphan EXCEL.EXE explicitly (branch 2 stop-gap), confirm the preceding activity completed (use its output, not a guessed delay), or restructure the workflow so the dependency is explicit.

- **"Wrap Write Range in a bare Try Catch and continue on error."** A bare Try-Catch that catches `Exception` / `BusinessException` / `COMException` and only logs without re-throwing turns Write Range failures into silent skips — the workflow proceeds as if the write succeeded, leaving the target workbook in a partial state. Downstream activities then operate on stale data, producing wrong outputs that are far harder to diagnose than the original exception. Use Try-Catch only with a real recovery path: retry with a smaller batch (branch 5 volume), mark the queue item Failed and abort, send a notification, or re-throw a domain-specific exception. The `Ignore empty source` property handles ONE specific case (branch 1's `Nothing`) — it is NOT a general "catch and continue" mechanism for any of the other branches.

- **"Set `ExcludeHeaders=True` to silence the empty-source error."** This is a real fix ONLY when the workflow's intent is to write data rows without a header. Setting `ExcludeHeaders=True` to make branch 3 "go away" while the rest of the workflow still expects a header row produces a workbook with misaligned data — the data lands in the same column positions as the header would have, so the first data row overwrites whatever was at that position. Either correctly skip the write when there are no rows (branch 3's `If`-guard fix), or restructure the workflow so the header / data contract is explicit.

- **"Downgrade `UiPath.Excel.Activities` to pre-2.8.5 to silence the hidden-rows error."** Branch 4's explicit error was added BECAUSE pre-2.8.5 versions silently wrote over hidden cells, causing data loss that workflow authors only discovered weeks later when human users unhid rows. Downgrading reintroduces the bug. The correct fix is to handle the hidden-rows case explicitly (unhide, restructure target range, or refactor).

## Prevention (cross-branch)

- Initialize all `DataTable` variables at declaration (e.g., `New DataTable()` assigned via `Variables` panel default value, OR an early `Build Data Table` on the execution path). Treat `Nothing` as never-valid for a DataTable in Write Range scope.
- Log `DataTable.Rows.Count` and `DataTable.Columns.Count` immediately before every Write Range. Two log lines are cheap insurance against branches 1 and 3.
- Guard Write Range with `If dt.Rows.Count > 0 Then` for any workflow where the source DataTable can legitimately be empty (filter results, query results, scraped data).
- Set `ReadOnly: False` explicitly on Modern `Use Excel File` scopes that contain any write activity. The default is a footgun.
- Avoid mixing Classic Workbook activities with Modern / Classic scope containers against the same workbook path in one workflow — the scope owns the file, and the standalone Workbook activity fails its own acquisition (branch 2's scope-conflict variant).
- For workflows on a sheet that humans also edit: before any Write Range, insert a `Remove Data Filter` (Modern) or equivalent Classic step. AutoFilter state is invisible to the workflow author at design time but very visible to the activity at runtime (branch 4).
- For workflows that aggregate or transform user-supplied content: sanitize formula-prefix characters (`=`, `+`, `-`, `@`) before writing. Treat any user-supplied string as potentially formula-shaped.
- For large-volume writes (>20K rows): default to OpenXML provider, chunk into 5–20K-row batches, log per-batch progress. Plan for the volume case even if today's data fits.

## Related

- Other Excel Activities failure fingerprints (read-side and write-side cross-cuts — file-locked, sheet-not-found, protected-sheet) are separate playbooks; see [`../summary.md`](../summary.md) for navigation. Branch 2 (file lock) and the sheet-name and protected-sheet pivots in step 2 inherit the diagnostic chains from those playbooks.
- [`./execute-macro-failures.md`](./execute-macro-failures.md) — sibling playbook for `Execute Macro` failures. Workflows that combine Write Range with VBA post-processing share the file-acquisition and scope-container surfaces.
- [`../overview.md`](../overview.md) — package overview, including the scope-container model and the OpenXML-vs-COM provider distinction relevant to branch 5's volume sub-cause.
- For headless workflows where the write target is best expressed in code rather than DataTable-to-range, consider migrating the relevant logic to the cloud surface via `o365-activities/` (Microsoft Graph API) — that surface has different memory semantics and no Excel COM dependency, avoiding branches 2, 4, and 5's volume variant entirely.
