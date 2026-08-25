---
confidence: high
---

# GSuite Sheets — 10 million cell limit exceeded

## Context

What this looks like — `GSuiteException` carrying a Google Sheets API 400 BadRequest:

`The service sheets has thrown an exception. HttpStatusCode is BadRequest. This action would increase the number of cells in the workbook above the limit of 10000000 cells.`

The job faults synchronously the moment the activity issues the write or expand request. The Google message portion is fixed by Google and is not produced by the activity package.

What activities can produce this error — any Sheets activity that writes cells or expands the grid:

**Modern Connections activities**:
- `WriteRangeConnections` — most common trigger; writing a DataTable to a range that extends past the current grid auto-expands the sheet
- `WriteCellConnections` — writing a single cell past the existing grid auto-expands rows/columns
- `WriteRowConnections` / `WriteColumnConnections` — writes that extend the grid past current bounds
- `AutoFillRangeConnections` — extends a pattern from a seed range; can expand the grid
- `CopyPasteRangeConnections` — paste destination can extend the grid
- `AddSheetConnections` — adds a new sheet. Default grid is 1000 × 26 = 26,000 cells, enough to trip the limit on a near-full spreadsheet

**Legacy activities**:
- `WriteCell`, `WriteRange`, `AppendRow` — same auto-expand triggers as the modern variants
- `AddNewSheet` — same 26,000-cell default grid as `AddSheetConnections`
- `AddDeleteColumns` (in *Add* mode), `AddDeleteRows` (in *Add* mode) — explicitly add N columns/rows to the grid
- `AutoFillRange`, `CopyPasteRange` — same expand triggers as the modern variants
- `CopySheet` ⚠️ — duplicates an entire sheet's cell grid in one shot; the most aggressive trigger and a **legacy-only** failure mode (no modern `*Connections` equivalent)
- `BatchUpdateValuesScope` — scope wrapper; the error reaches the user from this scope when one of the inner writes expands past the cap

What can cause it:
- The target spreadsheet is at or near Google's hard cap of 10,000,000 cells, and the activity issues a write or expand operation that would push it over. The cell count is the sum across all sheets in the spreadsheet, where each sheet's cell count is the rows × columns of its **bounded grid** — even empty cells inside the grid count.
- This is a hard Google Sheets quota and **cannot be raised** by the user, the workspace plan, or UiPath. The only path forward is to reduce the spreadsheet's cell count.

## Resolution

The error is unambiguous; no further investigation is needed. Stop the investigation and ask the user to free cells in the target spreadsheet before running the workflow again:

1. **Delete unused sheets** — every sheet (tab), even an empty one, contributes its full bounded grid to the total. Removing one default-sized sheet recovers 26,000 cells.
2. **Trim oversized grids** — sheets often have many empty rows or columns extending the bounded grid past the actual data. Resize the grid (delete trailing empty rows/columns) to drop the cell count without losing content.
3. **Archive into a new spreadsheet** — move historical sheets into a separate spreadsheet so the active one stays under the cap. This is the right answer when the data genuinely needs all those cells.
4. **Do not retry the workflow** until the user confirms cells have been freed. Re-running against a still-at-cap spreadsheet will produce the same exception.

If the activity in evidence is `BatchUpdateValuesScope`, identify which inner write triggered the expansion (the scope's failure message includes the offending range) — the resolution still applies to the spreadsheet as a whole, not to the scope.
