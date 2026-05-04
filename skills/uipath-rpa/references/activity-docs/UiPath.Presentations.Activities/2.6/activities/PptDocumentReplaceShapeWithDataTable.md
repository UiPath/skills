# Add Data Table to Slide

`UiPath.Presentations.Activities.PptDocumentReplaceShapeWithDataTable`

Inserts a data table into a presentation by replacing an empty placeholder or a previous DataTable. This activity can be used without Desktop PowerPoint installed and is faster than its Interop equivalent.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `SlideIndex` | Slide number | InArgument | `int` | Yes | | | Slide index that will be modified |
| `ShapeName` | Content placeholder | InArgument | `string` | Yes | | | Placeholder on the slide where the table will be created |
| `TableToInsert` | Table to add | InArgument | `DataTable` | Yes | | | The DataTable to insert into the slide |
| `FilePath` | Presentation (local path) | InArgument | `string` | Conditional | | | Presentation where to insert |
| `PathResource` | Presentation | InArgument | `IResource` | Conditional | | | Presentation where to insert |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ExcludeHeaders` | Exclude source headers | `bool` | `false` | If checked, the activity will not copy the first line of the source range |
| `AppendMode` | Behavior | `TableAppendMode` | `CreateNewTable` | How the table data should be added to the slide |
| `StartRow` | Overwrite starting in row | `int` | `0` | Overwrite data starting in a specified row (0 is the header row, 1 is the first data row) |
| `StartColumn` | Overwrite starting in column | `int` | `1` | Overwrite data starting in a specified column (1 is the first column) |

## Valid Configurations

This activity supports two file input modes (mutually exclusive via OverloadGroups):

**Mode A — Resource**: Set `PathResource` to an `IResource` handle.
**Mode B — Local Path**: Set `FilePath` to a local file path string.

### Enum Reference

**`TableAppendMode`**: `CreateNewTable` (Replace shape with new table), `AppendToTable` (Append data to existing table), `OverwriteExistingData` (Overwrite cells in existing table)

## XAML Example

```xml
<pres:PptDocumentReplaceShapeWithDataTable
    DisplayName="Add Data Table to Slide"
    SlideIndex="[1]"
    ShapeName="[&quot;Table Placeholder&quot;]"
    TableToInsert="[myDataTable]"
    FilePath="[&quot;C:\Presentations\report.pptx&quot;]"
    AppendMode="CreateNewTable"
    ExcludeHeaders="False" />
```

## Notes

- Does not require Desktop PowerPoint to be installed (uses OpenXML SDK)
- Cross-platform: works on both Windows and Linux
- `StartRow` and `StartColumn` are most relevant when `AppendMode` is `OverwriteExistingData`
