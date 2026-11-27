# For Each Row in Data Table

`UiPath.Core.Activities.ForEachRow`

Executes an action once for each row in the DataTable provided.

**Package:** `UiPath.System.Activities`
**Category:** Programming > DataTable

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| DataTable | Data Table | InArgument | DataTable | Yes | — | The DataTable whose rows will be iterated. |
| MaxIterations | Max Iterations | InArgument | Int32 | No | — | Maximum number of rows to process. Leave empty to iterate all rows. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| CurrentIndex | Current Index | OutArgument | Int32 | The zero-based index of the row currently being processed. |

## Notes

- This is a container activity. The **Body** sequence executes once for each row in the DataTable.
- Inside the body, the current row is available through the `CurrentRow` variable of type `DataRow`. The variable name is fixed and defined by the activity.
- `TypeArgument` is `DataRow`.
- `ColumnCount`, `ColumnNames`, and `ColumnSelectionType` are internal designer-state properties (`browsable: false`) used to render column binding hints in the designer body. They are not workflow arguments and should not be set manually.

## XAML Example

```xml
<ui:ForEachRow DisplayName="For Each Row in Data Table"
               DataTable="[myDataTable]"
               xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
               xmlns:sd="clr-namespace:System.Data;assembly=System.Data">
  <ui:ForEachRow.Body>
    <ActivityAction x:TypeArguments="sd:DataRow">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="sd:DataRow" Name="CurrentRow" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Body">
        <!-- Activities that reference CurrentRow go here -->
      </Sequence>
    </ActivityAction>
  </ui:ForEachRow.Body>
</ui:ForEachRow>
```
