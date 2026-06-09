---
confidence: medium
---

# Delete Range Failures

## Context

A `UiPath.Excel.Activities` `Delete Range` activity (Classic `DeleteRange` inside `Excel Application Scope`, or Modern `DeleteRangeX` inside `Use Excel File`) removes a rectangular range from a worksheet, optionally shifting remaining cells. Failures originate at one of five surfaces: structural (no enclosing scope), range syntax (malformed or empty `Range`), shift configuration (`ShiftCells` / `ShiftOption` conflict with range geometry), file acquisition (workbook locked / read-only), or row alignment (active AutoFilter hides rows in the target block).

What this looks like — Delete Range faults surface as one of these signatures:

- Studio shows a validation error on the activity, or the workflow throws at runtime before the activity executes — typically `BusinessException: Excel Application Scope not found` or a Modern equivalent. Branch 1.
- `System.ArgumentException: The range is invalid` or `System.ArgumentException: The string argument cannot be empty` — branch 2.
- `System.Runtime.InteropServices.COMException` from Excel referencing the shift operation, or `Application-defined or object-defined error` (`0x800A03EC`) raised when the shift direction conflicts with surrounding data — branch 3.
- `System.Runtime.InteropServices.COMException: Excel cannot access the file '<path>'` or `System.IO.IOException: The process cannot access the file ... because it is being used by another process.` — branch 4.
- The activity completes without an exception but the wrong rows are removed / remaining rows misalign, or a subsequent activity throws because expected rows are no longer where the workflow assumed — branch 5.

What can cause it (cause-branches — pick the right one from evidence):

1. **Activity outside an Excel scope container** — Classic `Delete Range` placed outside an `Excel Application Scope`, or Modern `Delete Range` placed outside a `Use Excel File`. Studio flags this as a design-time validation error; if the project was packaged anyway (e.g., validation suppressed, scope removed after publish), the workflow throws at runtime before the activity runs. See [`../overview.md`](../overview.md) for the scope model.
2. **Invalid range syntax or empty Range property** — `Range` is blank, quoted incorrectly, or uses non-A1 notation. Examples that fail: empty string, `Sheet1!A1:B10` (sheet prefix belongs in `SheetName`, not in `Range`), `R1C1:R10C2` (R1C1 notation), `A 1:B 10` (whitespace inside the address), unbalanced quotes from an expression that produced an empty literal. Same fault for both `A1:B10` (rectangular) and `A:E` / `1:10` (full-column / full-row) shapes — the syntax just has to parse.
3. **ShiftCells / ShiftOption conflict** — `ShiftCells` is True but `ShiftOption` is unset, set to a direction the range geometry cannot satisfy, or set to a direction that violates surrounding sheet structure (e.g., `ShiftUp` on a range whose bottom edge touches a merged region; `EntireRow` on a range that intersects a structured Table). Symptom: COMException with the Excel `Application-defined or object-defined error` text, sometimes with HRESULT `0x800A03EC`. May also manifest as a silent data corruption if Excel partially executed the shift before erroring.
4. **Workbook locked or opened read-only** — same fault family as Read Range / Write Cell file-locked: another process holds the workbook (orphan `EXCEL.EXE` from a prior job, a user has the file open in Excel UI, a different host has the lock on a network share), or the file is read-only at the OS layer (NTFS ACL, share-level permission, `Mark as Final`, Protected View on a downloaded copy). Delete Range is a write — read-only acquisition will fail it the same way it fails Write Range. The full investigation chain is shared with the read-range file-locked playbook; see [`../summary.md`](../summary.md) for navigation.
5. **Range misalignment over filtered data** — the worksheet has an active AutoFilter (`Data → Filter`) that hides rows in or around the target range. Delete Range operates on the cell coordinates as configured, not the visible rows; when shifting is enabled, hidden rows get pulled into the deletion or remaining rows shift onto cells the user expected to be empty. Symptom: activity completes without an exception, but post-condition checks fail or downstream activities see unexpected rows. May also throw if the filter range overlaps the deletion range in a way Excel's COM rejects.

What to look for:

- **The exception class and message** — first signal. `ArgumentException` with "range is invalid" / "argument cannot be empty" → branch 2. `BusinessException` referencing "Excel Application Scope" or "Use Excel File" → branch 1. `COMException` / `IOException` with "cannot access the file" → branch 4. `Application-defined or object-defined error` referencing shift / direction → branch 3. No exception but wrong output → branch 5.
- **Workflow source** — which `Delete Range` surface (Classic / Modern), the parent container (`Excel Application Scope` / `Use Excel File` / none), and the configured `Range`, `SheetName`, `ShiftCells`, `ShiftOption`. A literal `Range` value vs. an expression matters: branch 2 is most common when `Range` is an expression that resolved to empty / null at runtime.
- **Workbook state at fault time** — open in Excel by a user (Win32 GUI), held by orphan `EXCEL.EXE`, marked read-only, filtered with `Data → Filter` active. The `Data → Filter` toggle leaves a visible filter dropdown on the header row; check by opening the workbook before the workflow runs and confirming no funnel icons appear on column headers.
- **Sheet structure around the target range** — merged cells in or adjacent to the range, Excel Tables (`Ctrl+T` structured ranges) overlapping the range, freeze panes, named ranges that reference the deletion target. Any of these can convert a benign shift into a `0x800A03EC`.
- **Whether the intent is to clear data or restructure the sheet** — Delete Range with `ShiftCells: False` clears cell values (similar to `Clear Range` but also removes formats). If the workflow only needs to clear values without affecting cell layout / formatting, the correct activity is `Clear Range` — using Delete Range is a category error that surfaces as branches 3 or 5.

## Investigation

Go in this order — cheaper checks first.

1. **Capture the exact error, activity, and configuration.** From `uip or jobs get <job-key> --output json` → `Info`: exception class and full message. From workflow source: the `Delete Range` surface (Classic / Modern), parent container, configured `SheetName`, `Range`, `ShiftCells`, `ShiftOption`. From job logs (`uip or jobs logs <key>`): the activity's Trace lines for resolved runtime values.

2. **Branch the diagnostic on the exception signature.**
   - Studio validation error or `BusinessException` referencing the missing scope → branch 1; go to step 3.
   - `ArgumentException` with "range is invalid" / "argument cannot be empty" → branch 2; go to step 4.
   - `COMException` / `Application-defined or object-defined error` referencing shift / direction → branch 3; go to step 5.
   - `IOException` / `COMException` with "cannot access the file" / "used by another process" / "read-only" → branch 4; pivot to the read-range file-locked playbook for the full chain (see [`../summary.md`](../summary.md)).
   - No exception but wrong output / downstream failure → branch 5; go to step 6.
   - `BusinessException: The sheet with the name '<name>' does not exist` → cross-cutting sheet-name mismatch; pivot to the read-range sheet-not-found playbook for the full chain (see [`../summary.md`](../summary.md)). The diagnostic is identical to the read-side version.

3. **Confirm branch 1 (no scope container).** Inspect the workflow source. Trace the activity tree from `Delete Range` upward. The activity must have an ancestor that is either `Excel Application Scope` (Classic) or `Use Excel File` (Modern), with the configured `Workbook` / `WorkbookPath` matching the file Delete Range is meant to operate on. If the activity is at the root of the workflow, or inside a `Sequence` / `Try Catch` with no enclosing Excel scope, branch 1 is confirmed.

4. **Confirm branch 2 (invalid range syntax).** Examine the configured `Range` value:
   - If literal: check for empty string, unbalanced quotes, sheet prefix (`Sheet1!A1`), R1C1 notation, or whitespace inside the address. Valid forms: `"A1:B10"` (rectangle), `"A:E"` (full columns), `"1:10"` (full rows), `"A1"` (single cell).
   - If expression: log the resolved value immediately before the activity (`Log Message Level=Info Message=$"Range: '{rangeExpr}'"`) and rerun. The most common cause is an expression that produces an empty string from a null `DataRow` field, a `String.Format` against a `Nothing` value, or a slice that resolved to zero cells.
   - If the expression depends on values computed earlier in the workflow (`row counts`, `lastRow`), confirm those values are valid at the moment Delete Range runs. A `lastRow` of 0 with a range expression like `"A1:B" + lastRow.ToString` produces `"A1:B0"`, which Excel COM rejects.

5. **Confirm branch 3 (ShiftCells / ShiftOption conflict).** Inspect the activity configuration:
   - If `ShiftCells` is False, this branch does not apply — go back to step 2.
   - If `ShiftCells` is True, `ShiftOption` must be set to a valid direction. Classic `Delete Range` accepts `ShiftLeft` / `ShiftUp` / `EntireRow` / `EntireColumn`; Modern `DeleteRangeX` accepts `ShiftCellsLeft` / `ShiftCellsUp` / `EntireRow` / `EntireColumn` (naming differs slightly across versions — check the property dropdown for the host's package version).
   - Open the workbook in Excel and inspect the deletion target's surroundings: are there merged cells along the bottom edge (relevant for `ShiftUp`), the right edge (relevant for `ShiftLeft`), or anywhere Excel would need to break to perform the shift? Are there Excel Tables (`Ctrl+T`) overlapping the range? Excel Tables refuse partial-row deletions that would break the table's rectangular shape.
   - Reproduce manually: open the workbook in Excel, select the same range, `Home → Delete → Delete Cells…`, pick the same shift direction. If Excel rejects it interactively, the activity sees the same rejection wrapped in a COMException.

6. **Confirm branch 5 (filter misalignment).** Open the workbook in Excel before running the workflow, OR snapshot it from a recent backup:
   - Check each worksheet header row for the filter funnel icon (`Data → Filter` toggle). If active, the filter is applied — hidden rows exist.
   - `Home → Find & Select → Go To Special → Visible cells only` highlights what's visible. Compare to the configured Delete Range target: any hidden rows inside the range fall victim to the deletion silently.
   - For a workflow that builds the `Range` expression dynamically from a row count (`UsedRange.Rows.Count`), confirm whether the count includes hidden rows. The COM `UsedRange.Rows.Count` includes hidden rows; the modern OpenXML enumeration does not — provider-dependent skew.

The root cause must name **which of the five surfaces** the failure maps to, with the specific evidence: the exception text and class, the activity configuration (scope, `Range`, `ShiftCells`, `ShiftOption`), and the workbook state (locked / filtered / structured Tables / merged regions). A generic "Delete Range failed" is not a confirmed finding.

## Resolution

Map the branch identified in Investigation to the fix:

- **Branch 1 — Activity outside a scope container:**
  - Wrap the Delete Range activity in the correct scope. Classic `Delete Range` → place inside `Excel Application Scope` with the workbook configured on the scope. Modern `Delete Range` (`DeleteRangeX`) → place inside `Use Excel File` with the workbook configured on the scope.
  - Do not mix surfaces — a Classic Delete Range inside a Modern `Use Excel File` won't work, and vice versa. The toolbox shows them as separate entries; pick the one that matches the surrounding container.
  - Prevention: when refactoring workflows, do not delete an `Excel Application Scope` or `Use Excel File` container without auditing every Excel activity nested inside. Studio's design-time validation catches the resulting orphans, but only if validation is enabled and the file is reopened in Studio post-edit.

- **Branch 2 — Invalid range syntax or empty Range:**
  - Use standard A1 notation, quoted as a string literal in the activity property: `"A1:B10"` (rectangular block), `"A:E"` (entire columns), `"3:7"` (entire rows), `"A1"` (single cell). The sheet name goes in the separate `SheetName` property — never in `Range`.
  - Never leave `Range` blank. Excel COM has no concept of "delete nothing"; an empty string is a configuration error, not a noop.
  - For expression-based ranges: validate the resolved value before the activity. Add a `Log Message Level=Info Message=$"Range: '{range}'"` immediately before Delete Range. If the resolved value can be empty under any input, guard the activity with an `If` that skips the delete when the range is empty / invalid, or fix the expression so it never produces an invalid range.
  - For `lastRow`-style expressions: compute `lastRow` defensively. `If lastRow <= 0 Then` → skip; otherwise `Range = "A1:B" & lastRow.ToString`.
  - Prevention: prefer literal ranges where the deletion target is known at design time. Expression-based ranges are a runtime hazard that benefits from explicit validation.

- **Branch 3 — ShiftCells / ShiftOption conflict:**
  - **If the intent is to clear data while preserving cell layout / formatting**: set `ShiftCells` to False, OR replace Delete Range with `Clear Range`. Clear Range wipes cell values without affecting the surrounding sheet structure; it does not require a shift direction and does not interact with merged cells or structured Tables.
  - **If the intent is to remove cells and reflow surrounding data**: ensure `ShiftOption` matches the range shape and surrounding structure. `ShiftUp` requires that the rows below the range are not part of a merged region that crosses the deletion boundary. `EntireRow` deletes whole rows — preferred when the range spans full rows anyway, since Excel handles whole-row deletion more robustly than partial-row shifts.
  - **If the range intersects an Excel Table** (`Ctrl+T` structured range): use the table's own row-delete semantics rather than Delete Range. Workflow option: convert the table to a normal range (`Table Tools → Convert to Range`) before the deletion, then re-apply the table after, OR refactor to use a `Filter Range` followed by manual row removal.
  - Reproduce the operation manually in Excel to confirm the fix: open the workbook, select the configured range, `Home → Delete → Delete Cells…`, pick the same shift direction. If Excel performs the deletion cleanly, the activity will too.
  - Prevention: avoid `ShiftCells: True` on workbooks with structured Tables or merged regions adjacent to deletion targets. Use `EntireRow` deletes when the workflow's intent is row removal; the activity is more predictable than partial-row shifts.

- **Branch 4 — Workbook locked or read-only:**
  - Apply the resolution from the read-range file-locked playbook (see [`../summary.md`](../summary.md) for navigation). The write side (Delete Range) and the read side share the same fault surface — the file is held by another process, the lock is at the OS layer, or the file is on a network share whose semantics differ from local disk.
  - For workbooks marked read-only via `Mark as Final` or arriving via Protected View: open the file as the Robot user, remove the `Mark as Final` flag (`File → Info → Mark as Final`), or `Unblock-File '<path>'` to lift the Mark of the Web flag that triggers Protected View.
  - For Modern `Use Excel File` scopes: confirm `Read-only mode` is False on the scope. Default-True is a footgun that converts every write — including Delete Range — into a silent no-op or a confusing read-only-violation error.

- **Branch 5 — Range misalignment over filtered data:**
  - Remove the active filter before Delete Range. Insert a `Remove Data Filter` (Modern) or `Filter Range` with `Action: Remove` (Classic) before the Delete Range activity, targeting the same sheet. After the deletion, re-apply the filter if downstream activities expect it.
  - Alternative: have the workflow operate on filter-aware row identifiers (e.g., a key column) instead of cell coordinates. Read the filtered DataTable, identify rows by key, then delete rows by reapplying the filter and using `Delete Row` on individual matches — slower but correct under filtered conditions.
  - For workflows that compute the `Range` from a `UsedRange.Rows.Count`: be aware that this count is provider-dependent. The Modern OpenXML enumeration may differ from the Classic COM count when hidden rows are present. Validate the resolved range against the workbook's visible state before relying on it.
  - Prevention: workflows that mutate filtered workbooks should explicitly handle the filter state — either remove the filter before any range mutation, or operate on a filter-aware abstraction (DataTable + key matching) that doesn't depend on cell coordinates lining up.

## Anti-patterns (what NOT to do)

Common advice for Delete Range failures contains workarounds that hide bugs rather than fix them. The agent should NOT recommend any of these as a primary resolution.

- **"Add a `Delay` activity before Delete Range."** A `Delay` is a workaround for a race condition or initialization issue that the workflow author has not actually diagnosed. For Delete Range, the most common temptation is to add a Delay after opening the workbook (branch 4) or after a preceding filter operation (branch 5). The Delay "works" intermittently — it papers over branch 4 (the file lock from a prior orphan that happens to release within the delay window) or branch 5 (Excel's filter-change settling that COM exposes asynchronously). A reliable fix names the specific timing dependency: kill orphan EXCEL.EXE explicitly before the activity (branch 4 stop-gap), or remove the filter explicitly via the corresponding activity (branch 5). If a `Delay` is genuinely required, treat it as a diagnosis hint, document the dependency in a comment, and pick a duration an order of magnitude above the worst observed case.

- **"Wrap Delete Range in a Try Catch and continue on error."** A bare Try-Catch that catches `ArgumentException` / `COMException` / `System.Exception` and only logs without re-throwing turns Delete Range failures into silent skips — the workflow proceeds as if the deletion succeeded, leaving stale rows in the workbook. Downstream Read Range activities then process those stale rows as if they were new data, producing wrong outputs that are far harder to diagnose than the original exception. Use Try-Catch only with a real recovery path: fall back to `Clear Range` for branch 3, mark the queue item Failed for branch 4, send a notification, or re-throw a domain-specific exception.

- **"Use Delete Range when you only need to clear data."** Delete Range removes cells and (when `ShiftCells: True`) reflows surrounding data; `Clear Range` removes cell values while preserving cell layout, formatting, and surrounding structure. Workflows that only need to wipe values before a fresh Write Range should use Clear Range. Using Delete Range "because it sounded similar" is a category error that surfaces as branch 3 (shift conflicts) or branch 5 (misalignments) — the underlying bug is the wrong activity choice, not a configuration issue.

## Prevention (cross-branch)

- Confirm at design time that every `Delete Range` activity has an enclosing `Excel Application Scope` (Classic) or `Use Excel File` (Modern). Studio's validation catches the orphan case; do not suppress validation warnings on Excel activities.
- Use literal A1 ranges where the deletion target is known at design time. Expression-based ranges require explicit runtime validation (logging + skip-on-empty guards).
- Set `ShiftCells: False` unless the workflow specifically needs to reflow surrounding cells. The default-True is a frequent source of branch 3 failures on workbooks with structured Tables or merged regions.
- Use `Clear Range` instead of Delete Range when the intent is to wipe cell values without changing the sheet's structure. The activity is purpose-built for that case and avoids the shift / filter / table-intersection failure modes.
- For workflows that operate on filtered workbooks: explicitly remove the filter before any range mutation, then re-apply it after. Do not rely on Delete Range to handle filtered ranges correctly — it operates on coordinates, not visible rows.
- Provision Robot hosts with predictable Excel state — no `Personal.xlsb` interfering, no leftover orphan `EXCEL.EXE` from prior jobs (kill at job start as a hygiene step, not as a fix for branch 4), and write permissions on the workbook's containing folder for the Robot user.

## Related

- Other Excel Activities failure fingerprints (read-side and write-side cross-cuts — file-locked, sheet-not-found, protected-sheet) are separate playbooks; see [`../summary.md`](../summary.md) for navigation. Branches 4 (file lock) and the sheet-name pivot in step 2 inherit the diagnostic chains from those playbooks.
- [`../overview.md`](../overview.md) — package overview, including the scope-container model that branch 1 violates.
- For headless workflows where the deletion target is best expressed in code rather than cell coordinates, consider migrating the relevant logic to UiPath Data Manipulation activities (`Filter DataTable` / `Remove Data Row` / `For Each Row in DataTable`) operating on a `Read Range` result, then writing the modified `DataTable` back via `Write Range`. The DataTable round-trip avoids the in-place deletion failure modes entirely.
