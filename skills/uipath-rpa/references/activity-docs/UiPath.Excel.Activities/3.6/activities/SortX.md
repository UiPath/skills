# Sort Range

`UiPath.Excel.Activities.Business.SortX`

Sorts the data in a specified sheet, table, or range by one or more columns.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Range` | Range | InArgument | `IReadWriteRangeRef` | Yes | | Range to sort. |

### Configuration
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `HasHeaders` | Has headers | `bool` | `True` | First row in the range is a header row. |
| `AddSortColumn` | Add sort column | Action button | | Add a sort by column setting. Inserts a `SortColumnX` child activity. |

### Child Activity: `SortColumnX`

Each sort column is configured as a child `SortColumnX` activity inside the `SortX` body.

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ColumnName` | Column | InArgument | `string` | Yes | | The column to sort. |
| `SortDirection` | Direction | Property | `SortDirectionType` | No | `Ascending` | Sort order for the values in the column. |

## Enum Reference

### `SortDirectionType`
| Value | Description |
|-------|-------------|
| `Ascending` | Sort in ascending order (A-Z, smallest to largest). |
| `Descending` | Sort in descending order (Z-A, largest to smallest). |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <excel:SortX
    Range="[DataRange]"
    HasHeaders="True"
    DisplayName="Sort Range">
    <excel:SortX.Body>
      <ActivityAction x:TypeArguments="x:Object">
        <ActivityAction.Handler>
          <Sequence>
            <excel:SortColumnX
              ColumnName="[&quot;Name&quot;]"
              SortDirection="Ascending"
              DisplayName="Sort Column Configuration" />
          </Sequence>
        </ActivityAction.Handler>
      </ActivityAction>
    </excel:SortX.Body>
  </excel:SortX>
</excel:ExcelApplicationCard>
```

## Notes
- `SortX` is a container activity; one or more `SortColumnX` child activities must be added to define the sort criteria.
- Sort columns are applied in order -- the first child defines the primary sort, the second defines the secondary sort, etc.
- If no `SortColumnX` children are present, the activity throws an error.
- The `HasHeaders` property is not visible in the designer's property panel but is configurable in the activity card.
