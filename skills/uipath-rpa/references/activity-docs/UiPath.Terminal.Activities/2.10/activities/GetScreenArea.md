# Get Screen Area

`UiPath.Terminal.Advanced.Activities.TerminalGetScreenArea`

Reads all text within a rectangular region of the terminal screen, defined by a start position (Row/Column) and an end position (EndRow/EndColumn).

**Package:** `UiPath.Terminal.Activities`  
**Category:** App Integration.Terminals.Advanced  
**Required Scope:** `TerminalSession` — place inside a `TerminalSession.Body` `Sequence`. See [child-activity skeleton](TerminalSession.md#child-activity-skeleton) for a multi-activity example.

## Properties

### Position

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Row` | Row | `InArgument` | `int` | Yes | | Starting row of the region (1-based). |
| `Column` | Column | `InArgument` | `int` | Yes | | Starting column of the region (1-based). |
| `EndRow` | EndRow | `InArgument` | `int` | Yes | | Ending row of the region (1-based, inclusive). |
| `EndColumn` | EndColumn | `InArgument` | `int` | Yes | | Ending column of the region (1-based, inclusive). |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Text` | Text | `OutArgument` | `string` | The text read from the specified screen region. |

### Options

Standard `TimeoutMS` / `DelayMS` / `WaitType` (defaults `5000` / `300` / `READY`) — see [_common-options.md](TerminalSession/_common-options.md). Defaults work for typical sessions; tune only when scripted activities run faster than the host responds.

## Notes

### Extracting tabular data as a DataTable

`GetScreenArea` is the canonical building block for reading tabular screens (column-aligned host output, paged reports, etc.). The output is a single `string` with embedded newlines preserving the screen's row/column layout. Pipe that string through the **Generate Data Table** activity from `UiPath.System.Activities` to get a `DataTable` you can filter, write to Excel, or hand to other activities:

```xml
<uit:TerminalGetScreenArea DisplayName="Read inventory table"
                           Row="[5]" Column="[1]"
                           EndRow="[22]" EndColumn="[80]"
                           Text="[tableText]" />
<ui:GenerateDataTable DisplayName="Parse table"
                      Input="[tableText]"
                      DataTable="[inventory]"
                      ColumnSeparators="  "
                      NewLineSeparator="&#10;" />
```

Tuning notes for `GenerateDataTable`:

- **`ColumnSeparators`**: two or more spaces is usually correct for fixed-width column-aligned screens. Adjust if columns are tab-separated or pipe-separated.
- **`NewLineSeparator`**: `&#10;` (LF) is the default emission. Set to `&#13;&#10;` (CRLF) if the provider emits Windows-style newlines.
- **`PreserveFormatting`**: keep `true` so leading/trailing column padding is retained for short cells.
- **Header row**: if the screen's first row in the captured region is the column header, set `UseColumnHeaders=true`; otherwise pass `false` and rename columns post-hoc.

For non-tabular reads (a single value, a status line, free-form text), `GetText`, `GetTextAtPosition`, or `GetField` are the right tools — `GenerateDataTable` adds parsing overhead with no benefit.

## XAML Example

```xml
<uit:TerminalGetScreenArea DisplayName="Get Screen Area"
                           Row="[3]"
                           Column="[1]"
                           EndRow="[10]"
                           EndColumn="[80]"
                           Text="[areaText]"
                           WaitType="READY"
                           DelayMS="300" />
```
