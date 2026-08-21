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
| Filters | Filters | Property (List\<FilterOperationArgument\>) | — | The filter conditions built using the designer's Filter widget. Each condition specifies a column reference, an operator, an operand value, and a logical operator. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| OutputDataTable | Output Data Table | OutArgument | DataTable | The filtered DataTable result. |
| OutputFirstRow | Output First Row | OutArgument | DataRow | The first DataRow of the filtered result, for convenience. |

## Filter Conditions

Each row in the **Filters** list targets one column and applies one operator. Conditions can mix `And` and `Or`; `And` has higher precedence, then `Or` is applied across the resulting groups. The first condition's `BooleanOperator` is normalized to `And` at runtime.

### Column reference

The column for each condition is specified as an `InArgument` expression that evaluates to:
- A column **name** (String expression)
- A column **index** (Int32 expression)
- A **DataColumn** object expression
- A **GenericValue** expression that resolves to a supported column reference

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

- The `Filters` property is normally edited via the visual Filter widget in Studio Designer, but it is a regular `List<FilterOperationArgument>` and **can be authored directly in XAML** (see example below). The collection is annotated `[Browsable(false)]` on the activity but remains XAML-serializable.
- `FilterRowsMode` defaults to `Keep` when not specified.
- The activity produces a **new** DataTable in `OutputDataTable`; the original DataTable is not modified.
- Mixed `And` / `Or` chains are valid. The first condition's `BooleanOperator` is forced to `And`; later conditions keep their configured operators.
- The `Column` argument type must be one of `string` (column name), `int` (column index), `DataColumn`, or `GenericValue`. The framework validates this in `CacheMetadata`.

## XAML Example

Single condition — `Price > 1.99`, keep matching rows:

```xml
<ui:FilterDataTable DisplayName="Filter Data Table"
                    FilterRowsMode="Keep"
                    OutputDataTable="[filteredTable]"
                    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
                    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib"
                    xmlns:sd="clr-namespace:System.Data;assembly=System.Data.Common">
  <ui:FilterDataTable.DataTable>
    <InArgument x:TypeArguments="sd:DataTable">[myDataTable]</InArgument>
  </ui:FilterDataTable.DataTable>
  <ui:FilterDataTable.Filters>
    <scg:List x:TypeArguments="ui:FilterOperationArgument">
      <ui:FilterOperationArgument Operator="GT" BooleanOperator="And">
        <ui:FilterOperationArgument.Column>
          <InArgument x:TypeArguments="x:String">"Price"</InArgument>
        </ui:FilterOperationArgument.Column>
        <ui:FilterOperationArgument.Operand>
          <InArgument x:TypeArguments="x:Double">[1.99]</InArgument>
        </ui:FilterOperationArgument.Operand>
      </ui:FilterOperationArgument>
    </scg:List>
  </ui:FilterDataTable.Filters>
</ui:FilterDataTable>
```

`Operator` accepts the enum identifier names listed in the operator table above (`LT`, `GT`, `LTE`, `GTE`, `EQ`, `NOTEQ`, `EMPTY`, `NOTEMPTY`, `STARTSWITH`, etc. — not the symbol/display names).

`BooleanOperator` accepts `And` or `Or`. For an empty/not-empty operator, omit `<ui:FilterOperationArgument.Operand>` (no operand needed).
