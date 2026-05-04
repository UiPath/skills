# Format as Table

`UiPath.Excel.Activities.Business.CreateTableX`

Formats a range of cells as a table with a specified name.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Range` | Table range | InArgument | `IReadWriteRangeRef` | Yes | | Range to format as table. |
| `TableName` | Table name (optional) | InArgument | `string` | No | | Name of the new table. If left blank, a table name will be automatically generated. |

### Configuration
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `HasHeaders` | Has headers | `bool` | `True` | The first row of the range is used as a header row for the table. |
| `ReplaceExisting` | Replace existing | `bool` | `True` | If a table with this name already exists, it will be converted to a range so the new table can be created. |

### Output
| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `OutTableName` | Save new table name as | `string` | Name of the new table. |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <excel:CreateTableX
    Range="[MyRange]"
    TableName="SalesData"
    HasHeaders="True"
    ReplaceExisting="True"
    OutTableName="[CreatedTableName]"
    DisplayName="Format as Table" />
</excel:ExcelApplicationCard>
```

## Notes
- The table name must be a valid Excel name. If the provided name is invalid, an `ArgumentException` is thrown.
- When `ReplaceExisting` is `True` and a table with the specified name already exists, the existing table is first converted to a plain range before the new table is created.
- When `ReplaceExisting` is `False` and a table with the same name exists, an `ArgumentException` is thrown.
- If the range is an entire sheet, it is automatically clipped to the used range before table creation.
