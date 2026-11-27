# ReadRangeConnections

Generic type parameter: `System.Data.DataTable`

Key attributes:
- `Item` — spreadsheet selector; use Browse mode with `BrowserItemId` + `BrowserItem`
- `Range` — sheet name (e.g., `"Sheet1"`) or specific range (e.g., `"Sheet1!A1:D10"`)
- `HasHeaders` — `"True"` / `"False"`
- `ReadAs` — read mode (e.g., `"DataTable"`)
- Output: `Result` as `System.Data.DataTable`, `RangeInformation` as `UiPath.GSuite.Sheets.Models.RangeInformation`
