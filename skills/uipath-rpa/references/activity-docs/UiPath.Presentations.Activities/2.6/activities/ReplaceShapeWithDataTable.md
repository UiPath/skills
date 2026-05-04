# Add Data Table to Slide

`UiPath.Presentations.Activities.ReplaceShapeWithDataTable`

Inserts a data table into a presentation by replacing an empty placeholder or a previous DataTable, using the PowerPoint Interop API.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint.Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Presentation` | Presentation | InArgument | `IPresentationQuickHandle` | Yes | | | Presentation in which to insert the table |
| `SlideIndex` | Slide number | InArgument | `int` | Yes | | | Slide number on which to insert the table |
| `ShapeName` | Content placeholder | InArgument | `string` | Yes | | | Placeholder shape on the slide where the table will be created |
| `TableToInsert` | Table to add | InArgument | `DataTable` | Yes | | | The DataTable to insert into the slide |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ExcludeHeaders` | Exclude source headers | `bool` | `false` | If checked, the activity will not copy the first line of the source range |
| `AppendMode` | Behavior | `TableAppendMode` | `CreateNewTable` | How the table data should be added to the slide |
| `StartRow` | Overwrite starting in row | `int` | `0` | Overwrite data starting in a specified row (0 = header row, 1 = first data row) |
| `StartColumn` | Overwrite starting in column | `int` | `1` | Overwrite data starting in a specified column (1 = first column) |

### Enum Reference

**`TableAppendMode`**: `CreateNewTable` (Replace shape with new table), `AppendToTable` (Append data to existing table), `OverwriteExistingData` (Overwrite cells in existing table)

## XAML Example

```xml
<pres:ReplaceShapeWithDataTable
    DisplayName="Add Data Table to Slide"
    Presentation="[presentation]"
    SlideIndex="[1]"
    ShapeName="[&quot;Table Placeholder&quot;]"
    TableToInsert="[myDataTable]"
    AppendMode="CreateNewTable"
    ExcludeHeaders="False" />
```

## Notes

- Windows only — requires Desktop PowerPoint
- Must be placed inside a `PowerPointApplicationScope`
- `StartRow` and `StartColumn` are most relevant when `AppendMode` is `OverwriteExistingData`
