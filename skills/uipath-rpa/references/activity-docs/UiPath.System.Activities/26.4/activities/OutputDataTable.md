# Output Data Table as Text

`UiPath.Core.Activities.OutputDataTable`

Writes a DataTable object to a string using the CSV format.

**Package:** `UiPath.System.Activities`
**Category:** Programming > DataTable

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| DataTable | Data Table | InArgument | DataTable | Yes | — | The DataTable to convert to a CSV-formatted string. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| Text | Text | OutArgument | String | The resulting CSV string. Each row maps to a line; column values are comma-separated. |

## Notes

- The output uses CSV formatting: column values are separated by commas and each row ends with a newline.
- Column headers are included as the first line of the output string.

## XAML Example

```xml
<ui:OutputDataTable DisplayName="Output Data Table as Text"
                    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities">
  <ui:OutputDataTable.DataTable>
    <InArgument x:TypeArguments="sd:DataTable">[myDataTable]</InArgument>
  </ui:OutputDataTable.DataTable>
  <ui:OutputDataTable.Text>
    <OutArgument x:TypeArguments="x:String">[csvText]</OutArgument>
  </ui:OutputDataTable.Text>
</ui:OutputDataTable>
```
