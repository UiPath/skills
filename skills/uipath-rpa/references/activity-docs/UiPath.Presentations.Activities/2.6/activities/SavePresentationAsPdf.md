# Save Presentation as PDF

`UiPath.Presentations.Activities.SavePresentationAsPdf`

Exports a PowerPoint presentation to PDF format.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint.Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Presentation` | Presentation | InArgument | `IPresentationQuickHandle` | Yes | | | Presentation to save as PDF |
| `PdfPath` | Save as file | InArgument | `string` | Yes | | | The path where the PDF will be saved |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ReplaceExisting` | Replace existing | `bool` | `true` | If a file with this name already exists, replace it. Otherwise an error occurs |

## XAML Example

```xml
<pres:SavePresentationAsPdf
    DisplayName="Save as PDF"
    Presentation="[presentation]"
    PdfPath="[&quot;C:\Output\report.pdf&quot;]"
    ReplaceExisting="True" />
```

## Notes

- Windows only — requires Desktop PowerPoint
- Must be placed inside a `PowerPointApplicationScope`
