# Filter Data Table

`UiPath.Core.Activities.FilterDataTable`

Filters a DataTable by specifying conditions in the Filter widget. The activity can keep or delete rows according to the logical conditions that are specified in the properties.

**Package:** `UiPath.System.Activities`
**Category:** Programming > DataTable

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| DataTable | Data Table | InArgument | DataTable | No | — | The DataTable to filter. |
| FilterRowsMode | Filter Rows Mode | InArgument | SelectMode | No | — | Whether matching rows are kept or removed. See **Enum Reference** below. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| Filters | Filters | Property (List\<FilterOperationArgument\>) | — | The filter conditions built using the designer's Filter widget. Each condition specifies a column reference, an operator, and an operand value. Conditions are combined with a shared logical operator (AND or OR). |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| OutputDataTable | Output Data Table | OutArgument | DataTable | The filtered DataTable result. |
| OutputFirstRow | Output First Row | OutArgument | DataRow | The first DataRow of the filtered result, for convenience. |

## Filter Conditions

Each row in the **Filters** list targets one column and applies one operator. Conditions are all combined with the same logical operator (AND or OR) — mixed logical operators within a single filter set are not supported.

### Column reference

The column for each condition is specified as an `InArgument` expression that evaluates to:
- A column **name** (String expression)
- A column **index** (Int32 expression)
- A **DataColumn** object expression

### Supported filter operators

| Operator | Symbol / Name | Notes |
|----------|--------------|-------|
| `LT` | `<` | Numeric/comparable types |
| `GT` | `>` | Numeric/comparable types |
| `LTE` | `<=` | Numeric/comparable types |
| `GTE` | `>=` | Numeric/comparable types |
| `EQ` | `=` | Any type |
| `NOTEQ` | `!=` | Any type |
| `EMPTY` | Is Empty | No value operand required |
| `NOTEMPTY` | Is Not Empty | No value operand required |
| `STARTSWITH` | Starts With | String only |
| `ENDSWITH` | Ends With | String only |
| `CONTAINS` | Contains | String only |
| `NOTSTARTSWITH` | Does Not Start With | String only |
| `NOTENDSWITH` | Does Not End With | String only |
| `NOTCONTAINS` | Does Not Contain | String only |

## Enum Reference

### SelectMode

| Value | Description |
|-------|-------------|
| `Keep` | Rows matching the filter conditions are retained; all others are removed. |
| `Remove` | Rows matching the filter conditions are removed; all others are retained. |

## Notes

- The `Filters` property is populated via the visual Filter widget in Studio Designer — it is not intended to be set manually in XAML.
- `FilterRowsMode` defaults to `Keep` when not specified.
- The activity produces a **new** DataTable in `OutputDataTable`; the original DataTable is not modified.

## XAML Example

```xml
<ui:FilterDataTable DisplayName="Filter Data Table"
                    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities">
  <ui:FilterDataTable.DataTable>
    <InArgument x:TypeArguments="sd:DataTable">[myDataTable]</InArgument>
  </ui:FilterDataTable.DataTable>
  <ui:FilterDataTable.FilterRowsMode>
    <InArgument x:TypeArguments="ui:SelectMode">Keep</InArgument>
  </ui:FilterDataTable.FilterRowsMode>
  <ui:FilterDataTable.OutputDataTable>
    <OutArgument x:TypeArguments="sd:DataTable">[filteredTable]</OutArgument>
  </ui:FilterDataTable.OutputDataTable>
  <!-- Filters are configured via the visual widget in Studio -->
</ui:FilterDataTable>
```
