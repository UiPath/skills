# Add Text to Slide

`UiPath.Presentations.Activities.InsertTextInPresentation`

Inserts text into a placeholder using the PowerPoint Interop API.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint.Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Presentation` | Presentation | InArgument | `IPresentationQuickHandle` | Yes | | | Presentation where to insert |
| `SlideIndex` | Slide number | InArgument | `int` | Yes | | | The index of the slide containing the desired text form |
| `ShapeName` | Content placeholder | InArgument | `string` | Yes | | | The name of the shape where to insert |
| `Text` | Text to add | InArgument | `string` | Yes | | | Text to insert |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ClearExistingText` | Clear existing text in content placeholder | `bool` | `false` | If true, clears the text in the content placeholder before adding the new text |

## XAML Example

```xml
<pres:InsertTextInPresentation
    DisplayName="Add Text to Slide"
    Presentation="[presentation]"
    SlideIndex="[1]"
    ShapeName="[&quot;Title 1&quot;]"
    Text="[&quot;Quarterly Report&quot;]"
    ClearExistingText="True" />
```

## Notes

- Windows only — requires Desktop PowerPoint
- Must be placed inside a `PowerPointApplicationScope`
