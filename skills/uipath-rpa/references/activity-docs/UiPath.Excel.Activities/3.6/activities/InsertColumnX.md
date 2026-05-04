# Insert Column

`UiPath.Excel.Activities.Business.InsertColumnX`

Inserts a column in a sheet, table, or range at the specified location.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Range` | Range | InArgument | `IReadWriteRangeRef` | Yes | | Range in which the column will be inserted. |
| `RelativeColumnName` | Relative to column | InArgument | `string` | Yes | | Column next to which the new column will be inserted. |
| `RelativePosition` | Where to insert | Property | `ColumnRelativePosition` | Yes | | Before or after the 'Relative to column'. |
| `NewColumnName` | Add header | InArgument | `string` | No | | Value to use for the header row. |

### Configuration
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `HasHeaders` | Has headers | `bool` | `True` | The first row in the range is a header row. |

### Format Settings

This activity supports the **Data Type** format tab only (no Alignment or Font tabs). The `FormatType` selector is hidden since only one option is available.

#### Data Type Tab
| Name | Display Name | Type | Default | Visible When | Description |
|------|-------------|------|---------|------------|-------------|
| `CategoryType` | Category | `CellFormat` | `General` | Always (within Data Type tab) | The cell format category for the new column. |
| `NumberDecimalPlaces` | Decimals | `int` | `2` | CategoryType = Number | Number of decimal places. |
| `NumberUseThousandSeparator` | Use 1000 Separator | `bool` | `False` | CategoryType = Number | Use a thousand separator. |
| `CurrencyDecimalPlaces` | Decimals | `int` | `2` | CategoryType = Currency | Number of decimal places for currency. |
| `CurrencyUseThousandSeparator` | Use 1000 Separator | `bool` | `False` | CategoryType = Currency | Use a thousand separator for currency. |
| `CurrencySymbol` | Symbol | `string` | `$` | CategoryType = Currency | The currency symbol. |
| `CurrencySetAtTheEnd` | Set at the end | `bool` | `False` | CategoryType = Currency | Place the currency symbol after the value. |
| `PercentageDecimalPlaces` | Decimals | `int` | `2` | CategoryType = Percentage | Number of decimal places for percentage. |
| `DateType` | Date format | `DateType` | `Short` | CategoryType = Date | The date format to use. |
| `TimeType` | Time format | `TimeType` | `HoursMinutes` | CategoryType = Time | The time format to use. |
| `TimeIsAMPM` | AM/PM | `bool` | `False` | CategoryType = Time | Use 12-hour AM/PM format. |
| `CustomFormatAsString` | Custom format | `string` | `#,##0_);[Red](#,##0)` | CategoryType = Custom | A custom Excel format string. |

### Enum Reference

#### `ColumnRelativePosition`
| Value | Display Name |
|-------|-------------|
| `Before` | Before |
| `After` | After |

#### `CellFormat`
| Value | Display Name |
|-------|-------------|
| `General` | General |
| `Number` | Number |
| `Date` | Date |
| `Time` | Time |
| `Percentage` | Percentage |
| `Currency` | Currency |
| `Text` | Text |
| `Custom` | Custom |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <excel:InsertColumnX
    Range="[MyRange]"
    RelativeColumnName="Name"
    RelativePosition="After"
    NewColumnName="Email"
    HasHeaders="True"
    DisplayName="Insert Column">
    <excel:InsertColumnX.ColumnFormat>
      <excel:GeneralFormat />
    </excel:InsertColumnX.ColumnFormat>
  </excel:InsertColumnX>
</excel:ExcelApplicationCard>
```

## Notes
- The `ColumnFormat` property is not directly visible in the designer; instead, the designer shows a Data Type tab within the Format category.
- Unlike `FormatRangeX`, this activity only exposes the Data Type format settings (no Alignment or Font tabs), and the `FormatType` selector is hidden.
- When inserting into a table, the behavior differs slightly: the column is inserted relative to the table structure, and a header must be provided.
- The `RelativeColumnName` must reference an existing column in the range; otherwise, a runtime error occurs.
