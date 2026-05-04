# Filter

`UiPath.Excel.Activities.Business.FilterX`

Creates a filter in a range, table, or sheet based on the values in a single column. Can also be used to clear existing filters.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Range` | Source range | InArgument | `IReadWriteRangeRef` | Yes | | The sheet, range, or table to filter. |
| `ColumnName` | Column name | InArgument | `string` | Yes (when not clearing) | | The column containing the values to filter. Required when `ClearFilter` is `False`. When `ClearFilter` is `True`, if provided, only the specified column's filter is cleared; otherwise all filters are cleared. |

### Configuration
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ClearFilter` | Clear any existing filter | `bool` | `False` | Clear any existing filters already applied to the target range. |
| `UseAdvancedFilter` | Use advanced filter | `bool` | `False` | Switch between basic and advanced filter modes. Hidden when `ClearFilter` is `True`. |
| `BasicFilter` | Basic filter | `ExcelFilterSettings` | | A list of values to match against. Rows matching any of the listed values are shown. Visible when `ClearFilter` is `False` and `UseAdvancedFilter` is `False`. |
| `AdvancedFilter` | Advanced filter | `ExcelFilterSettings` | | One or two conditions using operators (e.g., equals, greater than, starts with) combined with a logical operator (And/Or). Visible when `ClearFilter` is `False` and `UseAdvancedFilter` is `True`. |

## Valid Configurations

- **Clear all filters:** Set `ClearFilter` to `True` and leave `ColumnName` empty.
- **Clear a specific column filter:** Set `ClearFilter` to `True` and specify `ColumnName`.
- **Basic filter:** Set `ClearFilter` to `False`, `UseAdvancedFilter` to `False`, and configure `BasicFilter` with a list of values.
- **Advanced filter:** Set `ClearFilter` to `False`, `UseAdvancedFilter` to `True`, and configure `AdvancedFilter` with one or two conditions.

### Enum Reference

#### `FilterMode`
| Value | Display Name |
|-------|-------------|
| `Basic` | Basic |
| `Advanced` | Advanced |

#### `LogicalOperator`
| Value | Display Name |
|-------|-------------|
| `And` | And |
| `Or` | Or |

#### `ExcelFilterOperator`
| Value | Display Name |
|-------|-------------|
| `NONE` | None |
| `LT` | < |
| `GT` | > |
| `LTE` | <= |
| `GTE` | >= |
| `EQ` | = |
| `NOTEQ` | != |
| `EMPTY` | Is Empty |
| `NOTEMPTY` | Is Not Empty |
| `STARTSWITH` | Starts With |
| `ENDSWITH` | Ends With |
| `CONTAINS` | Contains |
| `NOTSTARTSWITH` | Does Not Start With |
| `NOTENDSWITH` | Does Not End With |
| `NOTCONTAINS` | Does Not Contain |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <!-- Basic filter example -->
  <excel:FilterX
    Range="[MyRange]"
    ColumnName="Status"
    ClearFilter="False"
    DisplayName="Filter">
    <excel:FilterX.FilterArgument>
      <excel:FilterArgument Mode="Basic">
        <excel:FilterArgument.BasicFiltersArgument>
          <excel:BasicFilterArgument>
            <excel:BasicFilterArgument.BasicFilters>
              <InArgument x:TypeArguments="x:String">Active</InArgument>
              <InArgument x:TypeArguments="x:String">Pending</InArgument>
            </excel:BasicFilterArgument.BasicFilters>
          </excel:BasicFilterArgument>
        </excel:FilterArgument.BasicFiltersArgument>
      </excel:FilterArgument>
    </excel:FilterX.FilterArgument>
  </excel:FilterX>
</excel:ExcelApplicationCard>
```

## Notes
- The `FilterArgument` property is not directly visible in the designer; instead, the designer exposes `BasicFilter` and `AdvancedFilter` views.
- The `HasHeaders` property is always `True` and not exposed in the designer.
- When clearing filters, if `ColumnName` is omitted, all column filters on the range are cleared.
- The filter range cannot overlap any existing Excel tables.
- Advanced filter supports up to two conditions linked by an `And`/`Or` logical operator.
