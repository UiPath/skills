---
confidence: medium
---

# GSuite Sheets — Invalid range / unable to parse range

## Context

What this looks like — `GSuiteException` carrying a Google Sheets API 400 BadRequest:

`The service sheets has thrown an exception. HttpStatusCode is BadRequest. Invalid data[0]: Unable to parse range: <SheetName>!<CellRef>`

Common observed forms of `<CellRef>`:
- `A0`, `B0`, etc. — invalid row index (Sheets is 1-indexed; there is no row 0)
- empty string after the `!` — missing cell reference
- malformed column (e.g., special characters, lowercase letters mixed with numbers in invalid positions)
- bare cell with no sheet name on a multi-sheet spreadsheet

What activities can produce this error — any Sheets activity that takes a range or cell address in A1 notation, including:

**Modern activities**: `ReadCellConnections`, `ReadRangeConnections`, `ReadRowConnections`, `ReadColumnConnections`, `WriteCellConnections`, `WriteRangeConnections`, `WriteRowConnections`, `WriteColumnConnections`, `AutoFillRangeConnections`, `CopyPasteRangeConnections`, `DeleteRangeConnections`, `ForEachRowConnections`, `SetRangeColorConnections`, `GetCellColorConnections`.

**Legacy activities**: `ReadCell`, `ReadRange`, `ReadRow`, `ReadColumn`, `WriteCell`, `WriteRange`, `AutoFillRange`, `CopyPasteRange`, `ClearRange`, `DeleteRange`, `ForEachSheetRow`, `GetCellColor`.

What can cause it — Google's Sheets API rejected the supplied range string. Several possible causes:
- **1-indexing mistake** — the workflow references row `0` (e.g., `A0`, `Sheet1!A0`); Sheets row indices start at `1`. Most common when the range is built by string concatenation from a 0-based loop counter.
- **Empty or partial range** — the cell portion after `!` is empty, or the variable holding the range was null/empty at runtime.
- **Sheet name with special characters not quoted** — sheet names containing spaces, apostrophes, or non-ASCII characters require single quotes around the sheet name in A1 notation (e.g., `'Q1 2026'!A1`, not `Q1 2026!A1`).
- **Stale sheet reference** — the sheet was renamed or deleted after the workflow was authored, and the configured range still uses the old name.
- **Off-by-one in dynamic construction** — a variable used to build the cell address produced an out-of-bounds value (negative, zero, or extreme number).

## Investigation

1. From the workflow source, capture the exact range/cell expression configured on the activity and identify whether it is a literal string or a dynamic expression.
2. From the error message, extract the `<SheetName>!<CellRef>` portion — Google echoes back the exact range it failed to parse, so this is the authoritative input value at runtime.
3. Match the failed range against the cause list above:
   - Ends in `0` (e.g., `A0`) → 1-indexing mistake
   - Empty or just `!` after the sheet name → null/empty variable
   - Sheet name has spaces or special characters and is not single-quoted → quoting issue
   - Sheet name doesn't exist in the target spreadsheet → stale reference
4. If the range is dynamic, trace the upstream variable assignments to find where the bad value was produced.

## Resolution

- **1-indexing mistake**: change the row index to start at `1`. If the value comes from a loop counter, add `1` to the counter when building the address (or change the loop to start from `1`).
- **Empty/null range**: add a guard before the activity that fails the workflow with a clear message when the range variable is null/empty, rather than letting it reach the API.
- **Sheet name quoting**: wrap the sheet name in single quotes when it contains spaces or special characters: `'My Sheet'!A1`. The activity does not auto-quote.
- **Stale reference**: update the configured sheet name to match the spreadsheet's current sheet titles. Use `ForEachSheetConnections` or open the spreadsheet to confirm the actual sheet names.
- **Dynamic construction**: ensure the variable that builds the cell address is bounded (positive integer ≥ 1) and validated before use.

If the configured range is a literal that looks correct and the spreadsheet's sheet names match, ask the user to copy the range as it appears in the failed run's job arguments — the runtime value may differ from the design-time expression.
