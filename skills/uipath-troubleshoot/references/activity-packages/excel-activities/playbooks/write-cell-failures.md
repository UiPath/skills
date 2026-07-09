---
confidence: medium
---

# Write Cell Failures

## Context

A `UiPath.Excel.Activities` `Write Cell` activity (Classic Workbook surface, Classic `Excel Application Scope`, or Modern `Use Excel File`) writes a single value or formula to a target cell. Failures originate in one of four places: the file (locked by another process / wrong scope owns it), the cell target (sheet name mismatch, bad cell reference, protected target), the value (formula syntax rejected by Excel's parser), or the surrounding loop pattern (repeated Write Cell calls thrashing Excel's COM state).

What this looks like — Write Cell faults surface as one of these signatures:

- `System.IO.IOException: The process cannot access the file '<path>' because it is being used by another process.` — file lock, branch 1.
- `UiPath.Excel.BusinessException: The data you want to write has a wrong format, or Excel is busy.` — formula syntax (branch 2) or Excel state thrash (branch 3); same wording for two different causes, distinguish by context.
- `UiPath.Excel.BusinessException: The sheet with the name '<name>' does not exist.` — branch 4, identical signature to Read Range's sheet-not-found.
- `System.Runtime.InteropServices.COMException` with message about a protected sheet or read-only workbook — branch 5.
- `UiPath.Excel.BusinessException: The cell reference '<ref>' is invalid.` or `Application-defined or object-defined error` from Excel COM — branch 6, bad A1 notation / unknown named range.

What can cause it (cause-branches — pick the right one from evidence):

1. **Workbook locked OR Classic/Modern scope conflict** — A different process holds the file's lock, OR a Classic `Write Cell` (the standalone "Workbook" surface) targets a workbook that a surrounding `Excel Application Scope` / `Use Excel File` has already opened. The Classic Workbook surface accesses the file's raw bytes directly and refuses to write while any other process — including UiPath's own Excel COM scope — holds it. The error wording is the same `System.IO.IOException` as Read Range branch 1; the divergent fix is "stop mixing scopes" rather than "kill the locker."
2. **Formula syntax rejected** — The configured `Value` is a formula string (`=SUM(A1:A10)`, `=IF(...)`) that Excel's formula parser refuses. Three common causes: parameter separators (UiPath requires `,` even when the host's Windows regional setting expects `;`), unescaped or unbalanced quotes (string literals inside formulas need `""` around inner quotes when assembled from a UiPath VB.NET expression), or function names that depend on an add-in not loaded on the Robot's Excel session.
3. **Loop-induced "Excel is busy" / memory thrash** — `Write Cell` is called inside a `For Each Row` (or any tight loop) so the activity opens, writes, saves, and closes the workbook on every iteration. After ~100–500 iterations Excel COM accumulates COM-object leaks, the file lock churn races with itself, and the activity fails with the same "wrong format, or Excel is busy" wording as branch 2 — but here the wording is misleading: nothing's wrong with the data, the Excel instance is destabilized. Symptom: first N iterations succeed, then a sudden failure mid-loop; restarting the job gets through a different N iterations before failing again.
4. **Sheet name mismatch** — Configured `SheetName` does not match any sheet in the workbook. Verbatim the same diagnostic as the Read Range version — typos, OpenXML case-sensitivity, sheet renamed upstream, leading/trailing whitespace, look-alike Unicode characters, or a dynamic variable that resolved to the wrong value. See [`read-range-sheet-not-found.md`](./read-range-sheet-not-found.md) for the full investigation chain; the same diagnostic applies on the write side.
5. **Protected sheet or workbook** — The sheet has `Protect Sheet` enabled (with or without a password) or the workbook is opened read-only (file system ACL denies write, `Mark as Final` flag is on, the file came from email with `Protected View`, or the activity is running under a Modern `Use Excel File` scope with `Read-only mode: True`). Excel rejects the write with a COMException mentioning protection, or the activity returns silently with no observable change to the file.
6. **Invalid cell reference** — Configured `Cell` is malformed A1 notation (`AA0`, `B`, `1B`, leading whitespace), out of the workbook's bounds (`A1048577` exceeds the 1,048,576-row limit on `.xlsx`), or a named range that does not exist in the workbook's defined names. Same diagnostic as branch 4 (sheet mismatch) but at one level deeper: the sheet resolved, the cell reference inside it did not.

What to look for:

- **The exception class and message** — first signal. `IOException` → branch 1. "`wrong format, or Excel is busy`" → branch 2 or 3 (distinguish by loop context). "`sheet with the name`" → branch 4. COMException with "`protected`" / "`read-only`" → branch 5. "`cell reference`" / "`Application-defined or object-defined`" → branch 6.
- **Workflow source** — which `Write Cell` surface? Classic Workbook (no enclosing scope), Classic inside `Excel Application Scope`, or Modern `Write Cell` inside `Use Excel File`. The surface determines whether branch 1's scope-conflict variant applies.
- **The configured `Value`** — literal string vs. formula (`=…`). Branch 2 is only possible when the value is a formula.
- **Loop context** — is `Write Cell` inside `For Each` / `For Each Row` / `While`? Branch 3 is impossible outside a loop.
- **The configured `Cell`** — literal A1 notation, an expression, or a named range. Bad expressions are branch 6.
- **The workbook's protection state** — open the file in Excel; `Review → Protect Sheet` shows protection status; `File → Info` shows `Mark as Final` and `Protected View`. Branch 5 confirmation.
- **Job logs around the failure** — the activity's Trace logs echo the configured `Value` (truncated) and the resolved `Cell` / `SheetName`. Mismatches between source and resolved values point at branch 4 / 6 with a dynamic-expression cause.

## Investigation

Go in this order — cheaper checks first.

1. **Capture the exact error, activity, and target.** From `uip or jobs get <job-key> --output json` → `Info`: exception class and full message. From workflow source: the `Write Cell` surface (Classic Workbook / Classic inside scope / Modern), configured `SheetName`, `Cell`, and `Value` (literal or expression). Look at job logs (`uip or jobs logs <key>`) for the activity's Trace lines, which echo the resolved runtime values.

2. **Branch the diagnostic on the exception signature.**
   - `System.IO.IOException` → branch 1; go to step 3.
   - `BusinessException: ... sheet with the name '<x>' does not exist` → branch 4; see [`read-range-sheet-not-found.md`](./read-range-sheet-not-found.md). Done.
   - `BusinessException: ... wrong format, or Excel is busy` → branches 2 or 3; go to step 4.
   - `COMException` with "protected" / "read-only" / `0x800A03EC` near `Worksheet.Protect` → branch 5; go to step 5.
   - `BusinessException: ... cell reference '<x>' is invalid` or `Application-defined or object-defined error` → branch 6; go to step 6.

3. **Distinguish branch 1's two variants (lock vs. scope conflict).** If the activity is **Classic Workbook `Write Cell`** (no surrounding scope) and the workflow ALSO has an `Excel Application Scope` or `Use Excel File` for the same path elsewhere in the call graph, the scope-conflict variant applies — the Modern/Classic scope still holds the file when the Classic Workbook activity tries to write. Fix is structural (don't mix), not host-side (no killing required). If the Write Cell is the only Excel reference to that path, the issue is an external locker — pivot to [`read-range-file-locked.md`](./read-range-file-locked.md) for the full lock-investigation chain (orphan EXCEL.EXE, user editing, network share, AV scanner, concurrent jobs).

4. **Distinguish branch 2 from branch 3 (formula syntax vs. loop thrash).** Both surface with the "wrong format, or Excel is busy" wording.
   - If the activity is inside a `For Each` / `For Each Row` / `While` loop AND fails partway through (some iterations succeeded before the failure) → branch 3 (loop thrash). The misleading "wrong format" wording masks Excel COM instability. Confirm: `uip or jobs logs <key>` shows successful iterations preceding the fault.
   - If the activity is not in a loop, OR fails on the first iteration of a loop → branch 2 (formula syntax). Examine the configured `Value`. Formula? Inspect for:
     - Parameter separators: `=SUM(A1;A10)` is invalid; must be `=SUM(A1,A10)` regardless of host's Windows regional setting.
     - Quote escaping: in UiPath VB.NET, an inner string literal inside a formula expression needs doubled quotes. Source: `"=IF(A1=""x"",1,0)"` produces the formula `=IF(A1="x",1,0)` at runtime. Single quotes at the boundaries or unbalanced doubled quotes produce malformed formulas.
     - Function names: `=IFERROR(...)` and similar exist in modern Excel COM but not the OpenXML provider; functions from add-ins (e.g., `=BAHTTEXT(...)` from the Thai add-in) require the add-in registered for the Robot user.
   - If the value is not a formula and the activity is not in a loop → uncommon edge case; check for invisible characters in the `Value` itself (NBSP, BOM, control chars) before assuming Excel COM bug.

5. **Confirm branch 5 (protected sheet / workbook).** Open the workbook in Excel on the Robot user's profile (or have the user do so):
   - `Review → Protect Sheet` — if "Unprotect Sheet" is shown, the sheet is protected. The target cell may or may not be in the protected-cells range; check `Format Cells → Protection → Locked`.
   - `File → Info` — "Always Open Read-Only" or "Mark as Final" badges indicate workbook-level write blocks.
   - File system: `Get-Acl '<path>' | Format-List` confirms the Robot user has write permission. NTFS read-only or share-level read-only blocks the write at the OS layer.
   - If the workbook came from email or download: Excel's `Protected View` blocks writes until "Enable Editing" is clicked — a Robot session never clicks it.

6. **Confirm branch 6 (invalid cell reference).** Compare the configured `Cell` against:
   - A1 notation rules: column letters then row number, no whitespace, row ≥ 1, column within the workbook's column count (16,384 for `.xlsx`).
   - Workbook's defined names: open in Excel → `Formulas → Name Manager`, OR via PowerShell with `OpenXML SDK` if the host has it. The configured cell may be a named range that was renamed / deleted upstream.
   - Sheet-relative vs. workbook-relative: `Sheet1!A1` syntax is allowed in some surfaces but rejected in others; check whether the activity expects `Cell` to include the sheet prefix or whether the sheet comes from a separate property.

The root cause is **which of the six fault surfaces** (lock, scope conflict, formula syntax, loop thrash, protection, cell reference, sheet mismatch) the failure maps to. A confirmed finding names the surface (Classic Workbook / Classic scope / Modern scope), the resolved runtime values for `SheetName` / `Cell` / `Value`, and one of the cause-branches.

## Resolution

Map the branch identified in Investigation to the fix:

- **Branch 1 — Workbook locked OR Classic/Modern scope conflict:**
  - **Scope-conflict variant**: replace the standalone Classic Workbook `Write Cell` with one nested inside the surrounding scope. If the scope is Modern (`Use Excel File`), use Modern `Write Cell`. If the scope is Classic `Excel Application Scope`, use Classic `Write Cell` nested inside it. Do not mix Modern scopes with Classic Workbook activities — they own the file by different mechanisms.
  - **External locker variant**: the file is held by something outside the workflow. Follow [`read-range-file-locked.md`](./read-range-file-locked.md)'s investigation and resolution chain — orphan EXCEL.EXE kill, user-coordinated close, network-share unlock, AV exclusion, etc.
  - Stop-gap (any variant): add a `Kill Process` activity targeting `EXCEL` immediately before the failing `Write Cell` to terminate stragglers. Treat this as a diagnostic patch, not a permanent fix — it masks scope-cleanup bugs in the workflow.

- **Branch 2 — Formula syntax rejected:**
  - Replace semicolons with commas in parameter lists. UiPath passes the formula string to Excel verbatim and Excel COM requires commas regardless of the host's regional setting (the Excel UI displays semicolons in non-US locales, but the COM API does not).
  - Double-quote inner strings: `"=IF(A1=""hello"","""",A1)"` produces `=IF(A1="hello","",A1)`. Verify by logging the resolved formula (`Log Message Level=Info Message=$"Formula: {value}"`) before the Write Cell.
  - Confirm function availability: `=IFERROR` and other modern functions require Excel 2007+. Functions from add-ins (`=BAHTTEXT`, `=GETPIVOTDATA` against an unloaded PivotCache) need the add-in registered under the Robot user. Replace with primitive equivalents where possible.
  - For literal values (not formulas) that get misinterpreted as formulas — values starting with `=`, `+`, or `-` — prepend an apostrophe (`'`) or use the activity's `Preserve Format` property to force literal interpretation.

- **Branch 3 — Loop-induced "Excel is busy":**
  - Replace the cell-by-cell write pattern with bulk Write Range. Read the workbook into a `DataTable` once via `Read Range`, modify rows in memory inside the loop (`row("Column") = newValue`), then `Write Range` the modified table back to the workbook once after the loop. This collapses N file open/close cycles into 2.
  - If a per-cell pattern is unavoidable (e.g., the writes are interleaved with reads that depend on intermediate computed values), batch them: collect the writes into a `List<(string Cell, object Value)>` during the loop, then drain the list with a single Write Range or repeated Write Cell calls outside the loop where COM thrash is bounded.
  - Avoid `Save Workbook` inside the loop. Modern `Use Excel File` controls save semantics through the scope's `Auto Save` property; setting it to False and saving once at the end of the workflow eliminates per-iteration disk I/O.

- **Branch 4 — Sheet name mismatch:**
  - Apply the resolution from [`read-range-sheet-not-found.md`](./read-range-sheet-not-found.md). The write-side fix is identical to the read-side: correct the configured `SheetName`, match casing if on OpenXML, trim whitespace, normalize Unicode, or validate dynamic expressions against `Get Workbook Sheets` output at job start.

- **Branch 5 — Protected sheet or workbook:**
  - **Sheet protection**: unprotect via `Worksheet.Unprotect` before the write and re-protect after, OR remove protection from the sheet at the workbook source and replace it with per-cell `Locked: False` on the cells the workflow targets. Per-cell unlocking + sheet-wide protection is the safer pattern for production workbooks that humans also edit.
  - **Workbook read-only / Mark as Final**: open the workbook, remove the `Mark as Final` flag (`File → Info → Mark as Final`), or change file-system ACL to grant the Robot user write access. If the workbook arrived via Protected View (downloaded / emailed), have the publisher trust the source path or unblock the file (`Unblock-File '<path>'` on the Robot host).
  - **Modern scope with `Read-only mode: True`**: change the scope property to `False`. The default-True is a footgun on `Use Excel File` for workflows that include any Write activity.

- **Branch 6 — Invalid cell reference:**
  - Fix the A1 notation. Common typos: `B` instead of `B1`, `1B` instead of `B1`, trailing whitespace.
  - For named ranges: open the workbook in Excel → `Formulas → Name Manager` to confirm the name exists and points where expected. If the name was renamed upstream, update the activity. If the name is dynamic per-workbook, enumerate defined names at job start and validate.
  - For dynamic `Cell` expressions: log the resolved runtime value (`Log Message Level=Info Message=$"Cell: {cellExpr}"`) before the activity. Validate against the workbook's actual bounds (16,384 cols × 1,048,576 rows for `.xlsx`; `.xls` is smaller).

## Anti-patterns (what NOT to do)

Common quick-fixes for `Write Cell` failures hide the bug without fixing it. The agent should NOT recommend these as primary resolutions.

- **"Add a `Kill Process` activity for EXCEL before every Write Cell."** A blanket `Kill Process` masks scope-management bugs (branch 1 scope-conflict variant), terminates other legitimate Excel work on the host, and creates a brittle workflow that depends on the absence of Excel processes rather than correct scope ownership. Use `Kill Process` as a one-off diagnostic step to confirm a fix candidate, not as a recurring activity. The real fix for branch 1 is to align Modern/Classic scopes correctly; for branch 2/3 it's the formula or the loop pattern.

- **"Wrap the Write Cell in a Retry Scope to handle Excel-is-busy."** A Retry Scope around branch-3 (loop thrash) waits a few seconds and tries again — the underlying Excel COM state is still corrupt, and the retry compounds the damage. Worse, a Retry Scope around branch 2 (formula syntax) retries an invalid formula and either succeeds spuriously (Excel parses differently on the retry, masking the bug) or fails identically (wasted job time). Use Retry only with a real recovery action (re-open the workbook, reset COM state) AND only after diagnosing the underlying branch.

- **"Use `Continue On Error: True` on the Write Cell so the workflow doesn't fail."** Silently suppresses every fault surface — protected sheet, bad formula, missing cell reference, locked file — and the job completes "successfully" while producing wrong outputs. Branches 4 (sheet missing) and 5 (protection) most commonly drift into this anti-pattern because the failure looks "expected" when the workbook structure shifts. Treat any Excel write failure as a data-correctness incident, not a flake.

## Prevention (cross-branch)

- Pick one Excel surface per workflow and stay on it. New workflows: prefer Modern `Use Excel File` + nested Modern activities (`Write Cell` inside the scope). Existing workflows: do not mix Classic Workbook activities with Modern scopes — the surfaces own files differently and conflict.
- For any cell-by-cell write pattern, prefer Read Range → in-memory DataTable mutation → Write Range. Reserve `Write Cell` for single targeted writes (a header, a status flag, a timestamp) — not for bulk data.
- Validate formula strings before passing to Write Cell. Log the resolved formula; eyeball the separators and quote-escaping; consider building formulas via a helper function that asserts the comma-separator rule.
- Validate configured `SheetName` and `Cell` against the workbook's actual sheets / defined names at job start (`Get Workbook Sheets` + a quick `Read Cell` smoke test on the target). Fail fast with a clear message instead of letting a generic BusinessException surface mid-workflow.
- Author workbooks consumed by UiPath without sheet- or workbook-level protection when possible. If protection is required for human consumers, scope it to specific cell ranges and leave the Robot's target cells unlocked.
- Keep `UiPath.Excel.Activities` updated on a known-good version across the automation host fleet. Mismatched versions across hosts produce intermittent failures that look like branch 3 (Excel busy) but are package bugs; pinning the version in `project.json` and verifying it on each host eliminates this confound.
- Set `Auto Save: False` on `Use Excel File` for workflows that write inside loops; explicit `Save Workbook` outside the loop avoids per-iteration disk pressure.

## Related

- Branch 4 (sheet not found) shares its diagnostic with [`read-range-sheet-not-found.md`](./read-range-sheet-not-found.md) — the same investigation steps and resolutions apply on the write side.
- Branch 1's external-locker variant shares its diagnostic with [`read-range-file-locked.md`](./read-range-file-locked.md) — orphan EXCEL.EXE, user editing, network-share locks, AV/EDR scanners, and concurrent jobs all surface identically on Write Cell.
- For shared / cloud Excel workbooks accessed via Microsoft Graph rather than the local filesystem, see [`../../o365-activities/overview.md`](../../o365-activities/overview.md) — the Write Cell equivalents on the cloud surface have entirely different fault modes (auth, throttling, eTag conflicts) covered there.
