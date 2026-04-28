# Insert Chart

`UiPath.Excel.Activities.Business.InsertExcelChartX`

Inserts an Excel chart into a specified sheet based on data from a given range. Supports various chart categories and types with configurable dimensions and position.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Range` | Data range | InArgument | `IReadRangeRef` | Yes | | Data range to chart. |
| `InsertIntoSheet` | Insert into sheet | InArgument | `ISheetRef` | Yes | | The sheet in which to insert the chart. |
| `ChartCategory` | Chart category | Property | `ExcelChartCategory` | Yes | `Column` | Choose the chart to create based on the selected chart type. |
| `ChartType` | Chart type | Property | `ExcelChartType` | Yes | `xlColumnClustered` | Choose the chart to create based on the selected chart type. Available types depend on ChartCategory. |
| `ChartHeight` | Chart height | InArgument | `int` | Yes | (default) | Specify the height of the chart. Minimum enforced value is 50. |
| `ChartWidth` | Chart width | InArgument | `int` | Yes | (default) | Specify the width of the chart. Minimum enforced value is 50. |
| `Left` | Chart left | InArgument | `int` | Yes | (default) | Coordinates of how far to the right of the sheet the new chart will appear. |
| `Top` | Chart top | InArgument | `int` | Yes | (default) | Coordinates of how far below the top of the sheet the new chart will appear. |

### Output
| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `InsertedChart` | Save chart to | OutArgument | `IChartRef` | Saves the chart for use in other activities. |

## Conditional Behavior

- When `ChartCategory` changes, the available `ChartType` values are filtered to only those belonging to the selected category.
- If the current `ChartType` does not belong to the newly selected `ChartCategory`, `ChartType` is reset to the first type in the category.

### Enum Reference

#### `ExcelChartCategory`
| Value | Display Name |
|-------|-------------|
| `Area` | Area |
| `Bar` | Bar |
| `Column` | Column |
| `Line` | Line |
| `Pie` | Pie |
| `Scatter` | Scatter |

#### `ExcelChartType` (grouped by category)

**Area:** `xlArea`, `xlAreaStacked`, `xlAreaStacked100`
**Bar:** `xlBarClustered`, `xlBarStacked`, `xlBarStacked100`
**Column:** `xlColumnClustered`, `xlColumnStacked`, `xlColumnStacked100`
**Line:** `xlLine`, `xlLineMarkers`, `xlLineMarkersStacked`, `xlLineMarkersStacked100`, `xlLineStacked`, `xlLineStacked100`
**Pie:** `xlPie`, `xlDoughnut`
**Scatter:** `xlXYScatterSmoothNoMarkers`, `xlXYScatterSmooth`, `xlXYScatterLinesNoMarkers`, `xlXYScatterLines`, `xlXYScatter`

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Use Excel File">
  <excel:InsertExcelChartX
    Range="[dataRange]"
    InsertIntoSheet="[targetSheet]"
    ChartCategory="Column"
    ChartType="xlColumnClustered"
    ChartHeight="300"
    ChartWidth="500"
    Left="100"
    Top="50"
    InsertedChart="[chartOutput]"
    DisplayName="Insert Chart" />
</excel:ExcelApplicationCard>
```

## Notes
- The source range and destination sheet must be in the same workbook.
- If the width or height is less than 50, it is automatically increased to 50 at runtime.
- When the source range represents an entire sheet, the activity trims it to the used range before creating the chart.
- Pivot table ranges are excluded from the range selector.
