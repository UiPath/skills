---
confidence: high
---

# CV — Table cell-targeting failures (table not detected, row/column mismatch, old FeatureVersion)

## Context

What this looks like — the descriptor targets a table **cell** (`CellExtraInfo` set on `Descriptor.Target`), the find runs, retries to `TimeoutMS`, then faults with `UiPath.CV.ElementNotFoundException` carrying **one of nine cell-specific messages** (not the generic `Element not found`). One shared `FindCell` implementation raises all of them; the LAST cell error hit before timeout is rethrown via `ExceptionDispatchInfo`, so the author sees the specific cell message describing the final mismatch.

Match verbatim (variable parts parameterized as `<n>`):

- `Could not find table. Cell targeting supports only tables as target` — matched area is not a CV-detected **table**.
- `Table only contains <count> columns and column number is <n>` — `ColumnIndex` exceeds the detected column count.
- `Invalid column number <n>` — `ColumnIndex < 1` (index is **1-based**; `0` triggers this).
- `Table does not have any column with column name containing <name>` — `ColumnName` matched no header (exact → Levenshtein → contains all failed).
- `Table only contains <count> rows and row number is <n>` — `RowIndex` exceeds the detected row count.
- `Invalid row number <n>` — `RowIndex < 1` (1-based).
- `Table only contains <count> columns and cell number is <n>` — `RowSearchColumnIndex` (the search column for row-by-value) exceeds the column count.
- `Invalid cell number <n>` — `RowSearchColumnIndex < 1` (1-based).
- `No row in column <columnIndex> had a text containing <value>` — row-search value matched no cell in that search column. `<columnIndex>` is the **search column number**, not the value.

> **Pattern-matching trap:** the column/row "out of range" messages and the "invalid" (`< 1`) messages are distinct strings keyed on different conditions — `Table only contains <count> columns…` means the table was detected but is smaller than the index, while `Invalid column number 0` means a 1-based index was supplied as `0` or negative. Route on which sentence appears, not on "column problem" generically.

What activities can produce this:
- **CV Click** (`CvClickWithDescriptor`) — `Descriptor` whose target is a table cell.
- **CV Type Into** (`CvTypeIntoWithDescriptor`) — same.
- **CV Get Text** (`CvGetTextWithDescriptor`) — same (cell descriptor also drives a double-click extraction path).
- **CV Element Exists** (`CvElementExistsWithDescriptor`) — produces the same `ElementNotFoundException` internally, but the activity **catches it and returns `Result = false`**. The informative cell message is **lost at the workflow level** — visible only in the trace / CV runtime dump. See the silent-result trap in Investigation step 5.

What can cause it:
- **Old `Version` (FeatureVersion) — cell targeting disabled.** When the activity's `Version` property is below **V3**, `Feature.CellTargeting` is off; analysis falls back to `LegacyTableDetection` and the cell is never resolved against a modern table. The find returns null and faults with the **generic `Element not found`** message — NOT a cell-specific sentence. This is the trap: a correct cell descriptor on a downlevel `Version` looks like a plain not-found, not a cell error.
- **Table not detected as a table by the CV server.** The target area was matched, but the CV model did not classify it as a `Table`, so `GetTables` returns nothing for that area → `Could not find table. Cell targeting supports only tables as target`. Caused by rendering/border/styling changes, low resolution, or a grid the model reads as plain text.
- **Row/column index out of range.** The table is smaller than the descriptor's `ColumnIndex` / `RowIndex` / `RowSearchColumnIndex` (columns added/removed, fewer rows rendered than expected, header row counted or not).
- **1-based index supplied as 0 (or negative).** Cell indices are 1-based. `0` yields `Invalid column number 0` / `Invalid row number 0` / `Invalid cell number 0`.
- **Column-name / row-search-value mismatch.** `ColumnName` or `RowSearchValue` did not match the extracted header / cell text under exact, then Levenshtein-threshold, then contains matching. Header renamed, OCR misread, whitespace, or different language.
- **Row-index targeting after scrolling.** `RowIndex` cell targeting combined with a scrolled-to table is inherently unreliable — design-time emits the `ScrollWithRowIndex` warning. After scrolling, the row the model indexes may not be the row the author counted.

> **Different cause, do not apply this playbook:**
> - Generic `Element not found` with **no** cell sentence AND `Version >= V3` and a non-cell (image/control) target — the descriptor target itself never matched. Use [cv-element-not-found.md](./cv-element-not-found.md).
> - `Element not found` where the descriptor IS a cell but `Version < V3` is the suspected cause is handled **here** (Branch C below) — confirm `Version` before routing to cv-element-not-found.
> - `Descriptor or InputRegion is required`, `InvalidDescriptorException`, null `Target`, broken image refs — the descriptor never built. Use [cv-invalid-descriptor.md](./cv-invalid-descriptor.md).
> - Element was found, then the click/type failed (focus, stale coordinates, blocked input) — use [cv-action-failed-after-find.md](./cv-action-failed-after-find.md).
> - CV server / auth / throttling / OCR word-limit `System.ArgumentException` with a server error code — use [cv-server-auth-throttling-network.md](./cv-server-auth-throttling-network.md).
> - `CvElementExistsWithDescriptor` returning `false` for a cell config error, or any `ContinueOnError`/`InRegion` swallow — use [cv-silent-failures-and-false-results.md](./cv-silent-failures-and-false-results.md) for the false-result mechanics; return here for the cell descriptor fix itself.
> - Scrolled the whole screen / scroll never reached the pane — use [cv-scroll-search-failures.md](./cv-scroll-search-failures.md).
> - CV Get Text returned empty/stale/wrong text after the cell WAS found — use [cv-get-text-empty-or-wrong-result.md](./cv-get-text-empty-or-wrong-result.md).

## Investigation

1. **Read the exact exception message** from the job log / trace. Confirm it is `ElementNotFoundException` AND carries one of the nine cell sentences above. The specific sentence is the rethrown LAST mismatch after retries — it names the precise failing check.
2. **Confirm the descriptor targets a cell.** Inspect the faulted activity's `Descriptor` — `Target.CellExtraInfo` must be set (`UseColumnIndex`/`ColumnIndex`, `ColumnName`, `UseRowIndex`/`RowIndex`, `RowSearchColumnIndex`/`RowSearchValue`). No `CellExtraInfo` → this is not a cell-targeting failure; route to cv-element-not-found.
3. **Read the activity's `Version` property** from XAML. `Version < V3` (V1/V2/None, or a hand-edited XAML that lost the attribute) with a cell descriptor → Branch C, even if the message is the generic `Element not found`. This is the silent old-version trap and must be ruled out before treating it as a table-detection or index problem.
4. **Map the message to its check** to pick the branch (decision tree below). Each sentence corresponds to exactly one failing condition in `FindCell`.
5. **For `CvElementExistsWithDescriptor` returning `false`:** the cell message is swallowed. Pull it from the **CV runtime dump** (`*_ComputerVision` timestamped JSON written before the find gives up) or the activity trace span — that is the only place the `Invalid column number 0` / `Table only contains…` text survives. Do NOT conclude "element absent" from `Result = false` when the descriptor is a cell config — a config error and a genuinely-missing cell both return `false`.
6. **Check `ScrollDirection` + `RowIndex`.** If `ScrollDirection != None` and the cell uses `UseRowIndex`, the design-time `ScrollWithRowIndex` warning applies — row indices over scrolled tables drift.

## Resolution

Walk the decision tree. Choose the first branch whose evidence holds. Fixes that edit the descriptor/`Version` in the workflow are **interactive** — see Post-presentation actions.

### Branch A — Target is not detected as a table

Evidence: message is `Could not find table. Cell targeting supports only tables as target`. The area matched, but `GetTables` found no table for it.

Fix: the CV model did not classify the target as a `Table`. Re-validate the descriptor against the live screen — re-indicate the table so the model captures it as a table element. If borders/gridlines/styling changed, or resolution is low, restore the conditions under which the table is detectable. Confirm the indicated region actually encloses a tabular structure, not a styled list. No index change will help until the table is detected.

### Branch B — Index out of range or `< 1`

Evidence:
- `Table only contains <count> columns and column number is <n>` / `…rows and row number is <n>` / `…columns and cell number is <n>` → the table is smaller than the supplied index.
- `Invalid column number <n>` / `Invalid row number <n>` / `Invalid cell number <n>` with `<n>` `0` or negative → 1-based index supplied as `0`.

Fix:
- **For "only contains <count>…":** the actual table has `<count>` columns/rows. Correct the descriptor's `ColumnIndex` / `RowIndex` / `RowSearchColumnIndex` to be `<= <count>`. If the table genuinely gained/lost columns, the structure changed — re-confirm the intended cell.
- **For "Invalid … number 0":** indices are **1-based**. Change `0` to `1` (first column/row). Never use `0` for a CV cell index.

### Branch C — Old FeatureVersion (cell targeting disabled)

Evidence: descriptor has `CellExtraInfo` (step 2 confirmed) AND `Version < V3` (step 3). Message is typically the **generic `Element not found`**, NOT a cell sentence — because legacy table detection never matches the cell. Confirmed by Test `ActivityWithUiNode_WithCellDescriptor_OldVersion_Throws`.

Fix: set the activity's `Version` (FeatureVersion) to **V3 or later** so `Feature.CellTargeting` is enabled. Re-validate after the bump. Rule this branch OUT — and do NOT bump `Version` — when `Version` already reads V3+; in that case the generic `Element not found` is a real not-found (route to cv-element-not-found), not a cell-targeting trap.

### Branch D — Column-name or row-search-value mismatch

Evidence:
- `Table does not have any column with column name containing <name>` → `ColumnName` matched no header.
- `No row in column <columnIndex> had a text containing <value>` → `RowSearchValue` matched no cell in search column `<columnIndex>`.

Fix: the configured name/value did not match the extracted text under exact, Levenshtein, or contains matching. Compare the descriptor's `ColumnName` / `RowSearchValue` against the **actual extracted table text** in the CV dump. Correct for renamed headers, OCR misreads, whitespace, casing beyond threshold, or language. If the header is volatile, switch to index-based targeting (`UseColumnIndex` / `UseRowIndex`) instead of name/value.

### Branch E — Row-index targeting over a scrolled table

Evidence: `Table only contains <count> rows and row number is <n>` or a wrong cell hit, AND `ScrollDirection != None` with `UseRowIndex` (step 6; design-time `ScrollWithRowIndex` warning present).

Fix: row indices over scrolled tables are unreliable — the model re-indexes from the visible window after scrolling. Prefer **row-by-value** targeting (`RowSearchColumnIndex` + `RowSearchValue`) so the row is identified by content, not position, or remove the scroll dependency so the full table is in view before the find.

## Post-presentation actions

Branches A–E all end in a **workflow source edit** (descriptor `CellExtraInfo` change, `Version` bump, scroll/targeting change). This resolution path is **interactive**.

1. The orchestrator MUST call `AskUserQuestion` before any edit: print the exact file path, the activity `IdRef`, the property (e.g. `Version`, `Descriptor.Target.CellExtraInfo.ColumnIndex`), and the current → proposed value.
2. **Sharing a file path is not approval.** A path the user gave for reading does not authorize editing — issue a separate `AskUserQuestion` before writing.
3. Never bundle "gather input" with "apply fix" in one option — split into gather, then surface the concrete diff and confirm.
4. The apply-fix question must show the concrete diff (file, `IdRef`/line, current value, proposed value). Vague approvals are not enough.
5. One question per file/fix; list every file touched (XAML plus any Object Repository mirror).
6. If interactive approval is unavailable or errors: present the diff as a recommendation and stop. A recommendation-only close is acceptable; a silent edit never is.

## Stop / escalate

If the table IS detected (no `Cell targeting supports only tables` message), `Version >= V3`, the indices are within the detected `<count>` and `>= 1`, the column-name / row-search-value matches the extracted text, and no scrolled-row-index combination is present — yet the cell still cannot be resolved, the cause is outside cell targeting. Pull the CV runtime dump to confirm what the model extracted, then escalate (CV model table-extraction accuracy for this layout, or a server/analysis fault per [cv-server-auth-throttling-network.md](./cv-server-auth-throttling-network.md)) rather than continue under this playbook. Do NOT keep mutating indices once the dump shows the extracted table matches the descriptor.
