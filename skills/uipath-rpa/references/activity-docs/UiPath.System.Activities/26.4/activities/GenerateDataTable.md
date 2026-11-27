# Generate Data Table From Text

`UiPath.Core.Activities.GenerateDataTable`

Generate a DataTable from structured text.

**Package:** `UiPath.System.Activities`
**Category:** Programming > DataTable

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| Input | Input | InArgument | String | Yes* | — | The text to parse into a DataTable. Used with the **Use Text** overload group. |
| ContinueOnError | Continue On Error | InArgument | Boolean | No | — | If true, the workflow continues even if the activity throws an error. |

\* `Input` is required when using the text-based parsing mode. The **Use Positions** overload group uses `Positions` instead (for positional/fixed-width parsing from coordinate data, typically used with Digitizer outputs).

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| ParsingMethod | Parsing Method | Property (DataTableParsingMethod) | — | Determines how the text is split into columns. See **Enum Reference** below. |
| AutoDetectTypes | Auto Detect Types | Property (Boolean) | true | When true, column data types are inferred from the parsed values. |
| UseColumnHeader | Use Column Header | Property (Boolean) | false | When true, the first row of the text is treated as column headers. |
| UseRowHeader | Use Row Header | Property (Boolean) | false | When true, the first column is treated as row labels. |
| AllowMisalignedColumns | Allow Misaligned Columns | Property (Boolean) | false | When true, rows with a different number of columns than the header are accepted rather than causing an error. |
| ColumnSeparators | Column Separators | InArgument | String | — | Custom column delimiter string(s). Visible only when `ParsingMethod` is `Custom`. |
| NewLineSeparator | New Line Separator | InArgument | String | — | Custom row delimiter string. Visible only when `ParsingMethod` is `Custom`. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| DataTable | Data Table | OutArgument | DataTable | The DataTable generated from the parsed text. |

## Valid Configurations

| Mode | Required properties |
|------|-------------------|
| Parse from text | `Input` + `ParsingMethod` |
| Custom delimiters | `Input` + `ParsingMethod` = `Custom` + `ColumnSeparators` and/or `NewLineSeparator` |

## Enum Reference

### DataTableParsingMethod

| Value | Description |
|-------|-------------|
| `CSV` | Parses the input as comma-separated values. |
| `Custom` | Uses the values supplied in `ColumnSeparators` and `NewLineSeparator` to split the text. |

## Notes

- `CSVParsing` (`isVisible: false`) is a hidden legacy argument; use `ParsingMethod` instead.
- `PreserveNewLines` and `PreserveStrings` are hidden internal properties (`browsable: false`, `isVisible: false`) and should not be set manually.
- `ColumnSizes` and `Positions` support fixed-width / positional parsing flows (e.g. outputs from document digitization) and are not used in standard text-to-table scenarios.

## XAML Example

```xml
<ui:GenerateDataTable DisplayName="Generate Data Table From Text"
                      AutoDetectTypes="True"
                      UseColumnHeader="True"
                      ParsingMethod="CSV"
                      xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities">
  <ui:GenerateDataTable.Input>
    <InArgument x:TypeArguments="x:String">[csvText]</InArgument>
  </ui:GenerateDataTable.Input>
  <ui:GenerateDataTable.DataTable>
    <OutArgument x:TypeArguments="sd:DataTable">[resultTable]</OutArgument>
  </ui:GenerateDataTable.DataTable>
</ui:GenerateDataTable>
```
