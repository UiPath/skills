# Join Data Tables

`UiPath.Core.Activities.JoinDataTables`

Combines rows from two tables by using values common to each other, according to a Join rule.

**Package:** `UiPath.System.Activities`
**Category:** Programming > DataTable

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| DataTable1 | DataTable1 | InArgument | DataTable | Yes | — | The first (left) DataTable in the join. |
| DataTable2 | DataTable2 | InArgument | DataTable | Yes | — | The second (right) DataTable in the join. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| JoinType | JoinType | Property (JoinType) | — | The type of join to perform. See **Enum Reference** below. |
| Arguments | Arguments | Property (List\<JoinOperationArgument\>) | — | The join conditions built using the designer's Join widget. Each condition pairs a column from DataTable1 with a column from DataTable2 using a comparison operator. All conditions are combined with AND. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| OutputDataTable | Data Table | OutArgument | DataTable | The resulting joined DataTable. |

## Join Conditions

Each condition in **Arguments** references one column from each table and an operator. Only AND is supported as the logical operator between conditions.

### Column reference

Each side of a join condition is specified as an `InArgument` expression that evaluates to a column name (String), column index (Int32), DataColumn object, or GenericValue.

### Supported join operators

| Operator | Symbol |
|----------|--------|
| `LT` | `<` |
| `GT` | `>` |
| `LTE` | `<=` |
| `GTE` | `>=` |
| `EQ` | `=` |
| `NOTEQ` | `!=` |

## Enum Reference

### JoinType

| Value | Description |
|-------|-------------|
| `Inner` | Returns only rows where the join condition is satisfied in both tables. |
| `Left` | Returns all rows from DataTable1 and matched rows from DataTable2. Unmatched rows from DataTable2 produce null values in the result. |
| `Full` | Returns all rows from both tables. Rows without a match in the other table produce null values for the missing side. |

## Notes

- The `Arguments` property is normally edited via the visual Join widget in Studio Designer, but it is a regular `List<JoinOperationArgument>` and **can be authored directly in XAML** (see example below). It is annotated `[Browsable(false)]` on the activity but remains XAML-serializable.
- `Column1` and `Column2` are properties of each `JoinOperationArgument` (the join condition's left/right column references), not properties on the activity itself.
- The activity validates `Arguments` in `CacheMetadata`: at least one non-empty `JoinOperationArgument` is required. The `Column1` / `Column2` `InArgument` types must each resolve to `string` (column name), `int` (column index), `DataColumn`, or `GenericValue`.
- The output is always a new DataTable; neither input table is modified.

## XAML Example

Inner join — `employees.DepartmentId = departments.Id`:

```xml
<ui:JoinDataTables DisplayName="Join Data Tables"
                   JoinType="Inner"
                   OutputDataTable="[joinedTable]"
                   xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
                   xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib"
                   xmlns:sd="clr-namespace:System.Data;assembly=System.Data.Common">
  <ui:JoinDataTables.DataTable1>
    <InArgument x:TypeArguments="sd:DataTable">[employeesTable]</InArgument>
  </ui:JoinDataTables.DataTable1>
  <ui:JoinDataTables.DataTable2>
    <InArgument x:TypeArguments="sd:DataTable">[departmentsTable]</InArgument>
  </ui:JoinDataTables.DataTable2>
  <ui:JoinDataTables.Arguments>
    <scg:List x:TypeArguments="ui:JoinOperationArgument">
      <ui:JoinOperationArgument Operator="EQ">
        <ui:JoinOperationArgument.Column1>
          <InArgument x:TypeArguments="x:String">"DepartmentId"</InArgument>
        </ui:JoinOperationArgument.Column1>
        <ui:JoinOperationArgument.Column2>
          <InArgument x:TypeArguments="x:String">"Id"</InArgument>
        </ui:JoinOperationArgument.Column2>
      </ui:JoinOperationArgument>
    </scg:List>
  </ui:JoinDataTables.Arguments>
</ui:JoinDataTables>
```

`Operator` accepts the enum identifier names from the operator table above (`LT`, `GT`, `LTE`, `GTE`, `EQ`, `NOTEQ` — not the symbol/display names). Multiple `JoinOperationArgument` entries in the list are combined conjunctively (AND).
