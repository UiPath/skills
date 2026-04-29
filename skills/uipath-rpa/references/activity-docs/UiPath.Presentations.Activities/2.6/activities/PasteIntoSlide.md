# Paste Item into Slide

`UiPath.Presentations.Activities.PasteIntoSlide`

Pastes the clipboard content into a slide in a presentation.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint.Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Presentation` | Presentation | InArgument | `IPresentationQuickHandle` | Yes | | | Presentation in which to paste the item |
| `SlideIndex` | Slide number | InArgument | `int` | Yes | | | Slide number on which to paste the item |
| `ShapeName` | Content placeholder | InArgument | `string` | Yes | | | Placeholder shape on the slide where the item will be pasted |
| `Left` | Left | InArgument | `float?` | | | | How far right to move the item |
| `Top` | Top | InArgument | `float?` | | | | How far down to move the item |
| `Width` | Item width | InArgument | `float?` | | | | Width of the inserted item |
| `Height` | Item height | InArgument | `float?` | | | | Height of the inserted item |
| `NewShapeName` | New shape name | InArgument | `string` | | | | New name to assign to the shape |

## XAML Example

```xml
<pres:PasteIntoSlide
    DisplayName="Paste Item into Slide"
    Presentation="[presentation]"
    SlideIndex="[1]"
    ShapeName="[&quot;Content Placeholder&quot;]"
    Width="[400.0F]"
    Height="[300.0F]" />
```

## Notes

- Windows only — requires Desktop PowerPoint
- Must be placed inside a `PowerPointApplicationScope`
- Requires content to already be on the clipboard before this activity runs
- Position and size are optional; when omitted, uses the placeholder's dimensions
