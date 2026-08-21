# Sort Data Table

`UiPath.Core.Activities.SortDataTable`

Sorts a DataTable by ascending or descending order, based on the values of a specified column.

**Package:** `UiPath.System.Activities`
**Category:** Programming > DataTable

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| DataTable | Ascending | InArgument | DataTable | Yes | — | The DataTable to sort. |
| ColumnName | Name | InArgument | String | Yes* | — | The name of the column to sort by. Mutually exclusive with **Index** and **Column**. |
| ColumnIndex | Index | InArgument | Int32? | Yes* | — | The zero-based index of the column to sort by. Mutually exclusive with **Name** and **Column**. |
| DataColumn | Column | InArgument | DataColumn | Yes* | — | A DataColumn object identifying the column to sort by. Mutually exclusive with **Name** and **Index**. |

\* Exactly one of `ColumnName`, `ColumnIndex`, or `DataColumn` must be provided. Providing none or more than one is a validation error.

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| SortOrder | Order | Property (SortOrder) | — | The sort direction. See **Enum Reference** below. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| OutputDataTable | Data Table | OutArgument | DataTable | A new DataTable containing the sorted rows. The original DataTable is not modified. |

## Valid Configurations

| Mode | Required properties |
|------|-------------------|
| Sort by column name | `DataTable` + `ColumnName` + `SortOrder` |
| Sort by column index | `DataTable` + `ColumnIndex` + `SortOrder` |
| Sort by DataColumn object | `DataTable` + `DataColumn` + `SortOrder` |

## Enum Reference

### SortOrder

| Value | Description |
|-------|-------------|
| `Ascending` | Sorts rows from lowest to highest value. |
| `Descending` | Sorts rows from highest to lowest value. |

## XAML Example

```xml
<ui:SortDataTable DisplayName="Sort Data Table"
                  SortOrder="Ascending"
                  xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities">
  <ui:SortDataTable.DataTable>
    <InArgument x:TypeArguments="sd:DataTable">[myDataTable]</InArgument>
  </ui:SortDataTable.DataTable>
  <ui:SortDataTable.ColumnName>
    <InArgument x:TypeArguments="x:String">"LastName"</InArgument>
  </ui:SortDataTable.ColumnName>
  <ui:SortDataTable.OutputDataTable>
    <OutArgument x:TypeArguments="sd:DataTable">[sortedTable]</OutArgument>
  </ui:SortDataTable.OutputDataTable>
</ui:SortDataTable>
```
