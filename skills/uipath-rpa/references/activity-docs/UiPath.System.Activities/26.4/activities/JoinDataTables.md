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

Each side of a join condition is specified as an `InArgument` expression that evaluates to a column name (String), column index (Int32), or DataColumn object.

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

- The `Arguments` property is populated via the visual Join widget in Studio Designer — it is not intended to be set manually in XAML.
- `Column1` and `Column2` are internal designer-state properties (zero-based column counts) that track the column layout in the widget. They are not workflow arguments.
- `Operation` is an internal property holding the join rule at runtime; it is not exposed as a designer argument.
- The output is always a new DataTable; neither input table is modified.

## XAML Example

```xml
<ui:JoinDataTables DisplayName="Join Data Tables"
                   JoinType="Inner"
                   xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities">
  <ui:JoinDataTables.DataTable1>
    <InArgument x:TypeArguments="sd:DataTable">[employeesTable]</InArgument>
  </ui:JoinDataTables.DataTable1>
  <ui:JoinDataTables.DataTable2>
    <InArgument x:TypeArguments="sd:DataTable">[departmentsTable]</InArgument>
  </ui:JoinDataTables.DataTable2>
  <ui:JoinDataTables.OutputDataTable>
    <OutArgument x:TypeArguments="sd:DataTable">[joinedTable]</OutArgument>
  </ui:JoinDataTables.OutputDataTable>
  <!-- Join conditions are configured via the visual widget in Studio -->
</ui:JoinDataTables>
```
