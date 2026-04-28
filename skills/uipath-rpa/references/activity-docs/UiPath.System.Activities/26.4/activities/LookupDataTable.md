# Lookup Data Table

`UiPath.Core.Activities.LookupDataTable`

This activity searches for the value provided in the Lookup Value property inside the DataTable and returns the row index of the found cell. If the Target Column is set, it also returns the value from the cell with the specified Row.

**Package:** `UiPath.System.Activities`
**Category:** Programming > DataTable

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| DataTable | Data Table | InArgument | DataTable | Yes | — | The DataTable to search. |
| LookupValue | Lookup Value | InArgument | String | Yes | — | The value to search for within the lookup column. |
| LookupColumnName | Column Name | InArgument | String | Yes* | — | The name of the column to search in. Mutually exclusive with **Column Number** (lookup). |
| LookupColumnIndex | Column Number | InArgument | Int32? | Yes* | — | The zero-based index of the column to search in. Mutually exclusive with **Column Name** (lookup). |
| TargetColumnName | Column Name | InArgument | String | No | — | The name of the column from which to retrieve the cell value at the found row. Mutually exclusive with **Column Number** (target). |
| TargetColumnIndex | Column Number | InArgument | Int32? | No | — | The zero-based index of the column from which to retrieve the cell value. Mutually exclusive with **Column Name** (target). |

\* Exactly one of `LookupColumnName` or `LookupColumnIndex` must be provided. `LookupDataColumn` (a DataColumn object overload) exists in the source but is hidden (`isVisible: false`) and is not exposed in the designer UI.

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| RowIndex | RowIndex | OutArgument | Int32 | The zero-based index of the row where the lookup value was found. Returns `-1` if not found. |
| CellValue | CellValue | OutArgument | Object | The value of the cell at the found row in the target column. Only populated when a target column is specified. |

## Valid Configurations

### Lookup column reference modes

| Mode | Property to set |
|------|----------------|
| By column name | `LookupColumnName` |
| By column index | `LookupColumnIndex` |

### Target column reference modes (optional)

| Mode | Property to set |
|------|----------------|
| By column name | `TargetColumnName` |
| By column index | `TargetColumnIndex` |
| No target column | Leave both empty — only `RowIndex` is populated |

## Notes

- `LookupDataColumn` (overload group `Lookup data column`) is present in the activity but hidden in the designer (`isVisible: false`). Use `LookupColumnName` or `LookupColumnIndex` instead.
- `TargetDataColumn` (target column DataColumn object) is similarly hidden (`isVisible: false`). Use `TargetColumnName` or `TargetColumnIndex` instead.
- `RowIndex` is `-1` when the lookup value is not found.
- `CellValue` is `null` when no target column is specified or when the lookup value is not found.

## XAML Example

```xml
<!-- Lookup by column name, retrieve value from target column by name -->
<ui:LookupDataTable DisplayName="Lookup Data Table"
                    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities">
  <ui:LookupDataTable.DataTable>
    <InArgument x:TypeArguments="sd:DataTable">[myDataTable]</InArgument>
  </ui:LookupDataTable.DataTable>
  <ui:LookupDataTable.LookupValue>
    <InArgument x:TypeArguments="x:String">"Alice"</InArgument>
  </ui:LookupDataTable.LookupValue>
  <ui:LookupDataTable.LookupColumnName>
    <InArgument x:TypeArguments="x:String">"FirstName"</InArgument>
  </ui:LookupDataTable.LookupColumnName>
  <ui:LookupDataTable.TargetColumnName>
    <InArgument x:TypeArguments="x:String">"Department"</InArgument>
  </ui:LookupDataTable.TargetColumnName>
  <ui:LookupDataTable.RowIndex>
    <OutArgument x:TypeArguments="x:Int32">[foundRowIndex]</OutArgument>
  </ui:LookupDataTable.RowIndex>
  <ui:LookupDataTable.CellValue>
    <OutArgument x:TypeArguments="x:Object">[departmentValue]</OutArgument>
  </ui:LookupDataTable.CellValue>
</ui:LookupDataTable>
```
