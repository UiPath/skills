# Filter Pivot Table

`UiPath.Excel.Activities.Business.FilterPivotTableX`

Applies a filter to a specified column of a pivot table, or clears any existing filter on that column.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Table` | Pivot table to filter | InArgument | `IPivotTableRef` | Yes | | The pivot table to filter. |
| `ColumnName` | Column name | InArgument | `string` | Yes | | The column used as a filter in the pivot table. |

### Options
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ClearFilter` | Clear any existing filter | Property | `bool` | No | `False` | Clear any existing filters applied to the target range. |

### Designer Controls
| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `BasicFilter` | Basic filter | `ExcelFilterSettings` (NotMapped) | Configures the filter values to apply. Only visible when ClearFilter is False. |

### Internal
| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `FilterArgument` | (hidden) | Property | `FilterArgument` | Stores the filter configuration. Not visible in the designer. |

## Conditional Visibility

- `BasicFilter` is hidden when `ClearFilter` is `True`.
- `FilterArgument` is always hidden (serialized internally).

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Use Excel File">
  <excel:FilterPivotTableX
    Table="[pivotTableRef]"
    ColumnName="Region"
    ClearFilter="False"
    DisplayName="Filter Pivot Table">
    <excel:FilterPivotTableX.FilterArgument>
      <excel:FilterArgument>
        <excel:FilterArgument.BasicFiltersArgument>
          <excel:BasicFiltersArgument>
            <!-- filter values configured here -->
          </excel:BasicFiltersArgument>
        </excel:FilterArgument.BasicFiltersArgument>
      </excel:FilterArgument>
    </excel:FilterPivotTableX.FilterArgument>
  </excel:FilterPivotTableX>
</excel:ExcelApplicationCard>
```

### Clear filter variant
```xml
<excel:ExcelApplicationCard DisplayName="Use Excel File">
  <excel:FilterPivotTableX
    Table="[pivotTableRef]"
    ColumnName="Region"
    ClearFilter="True"
    DisplayName="Clear Pivot Table Filter" />
</excel:ExcelApplicationCard>
```

## Notes
- The `ColumnName` is required and validated at design time; an error is shown if it is empty.
- When `ClearFilter` is `False`, at least one filter value must be provided; otherwise a validation error occurs.
- The pivot table must exist on the specified worksheet; otherwise an `ArgumentException` is thrown.
- The pivot table reference must include a valid address, worksheet, and parent handle.
