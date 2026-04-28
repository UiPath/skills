# Save PowerPoint File As

`UiPath.Presentations.Activities.SavePresentationFileAs`

Saves a PowerPoint file as a new file in the specified format.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint.Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Presentation` | Presentation | InArgument | `IPresentationQuickHandle` | Yes | | | Presentation to save |
| `FilePath` | Save as file | InArgument | `string` | Yes | | | Name and location of the new file |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `SaveAsFileType` | Save as type | `PresentationSaveAsType` | `XmlPresentation` | Format to save the presentation |
| `ReplaceExisting` | Replace existing | `bool` | `true` | If a file with this name already exists, replace it. Otherwise an error occurs |

### Enum Reference

**`PresentationSaveAsType`**: `XmlPresentation` (.pptx format), `MacroEnabledPresentation` (.pptm format), `OldPresentation` (.ppt legacy format)

## XAML Example

```xml
<pres:SavePresentationFileAs
    DisplayName="Save PowerPoint File As"
    Presentation="[presentation]"
    FilePath="[&quot;C:\Output\report_copy.pptx&quot;]"
    SaveAsFileType="XmlPresentation"
    ReplaceExisting="True" />
```

## Notes

- Windows only — requires Desktop PowerPoint
- Must be placed inside a `PowerPointApplicationScope`
- The correct file extension is automatically appended based on `SaveAsFileType` if `FilePath` does not already end with it (e.g., saving as `XmlPresentation` with path `C:\report` produces `C:\report.pptx`)
