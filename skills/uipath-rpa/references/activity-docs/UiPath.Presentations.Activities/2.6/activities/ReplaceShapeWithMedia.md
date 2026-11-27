# Add Image/Video to Slide

`UiPath.Presentations.Activities.ReplaceShapeWithMedia`

Replaces a placeholder shape with a media element (image or video) using the PowerPoint Interop API.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint.Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Presentation` | Presentation | InArgument | `IPresentationQuickHandle` | Yes | | | Presentation in which to do the replacement |
| `SlideIndex` | Slide number | InArgument | `int` | Yes | | | The index of the slide on which to do the replacement |
| `ShapeName` | Shape Name | InArgument | `string` | Yes | | | The name of the shape to replace with media |
| `Media` | Image/Video file | InArgument | `string` | Yes | | | Media to use for replacement. Must be a valid absolute file path to an existing file |
| `NewShapeName` | New Shape Name | InArgument | `string` | | | | The new name to assign to the shape selected |
| `Left` | Left | InArgument | `float?` | | | | Specify how far right to move the item (points). Must not be negative |
| `Top` | Top | InArgument | `float?` | | | | Specify how far down to move the item (points). Must not be negative |
| `Width` | Item width | InArgument | `float?` | | | | Width of the inserted item (points). Must not be less than 50 |
| `Height` | Item height | InArgument | `float?` | | | | Height of the inserted item (points). Must not be less than 50 |

## XAML Example

```xml
<pres:ReplaceShapeWithMedia
    DisplayName="Add Image to Slide"
    Presentation="[presentation]"
    SlideIndex="[1]"
    ShapeName="[&quot;Picture Placeholder&quot;]"
    Media="[&quot;C:\Images\chart.png&quot;]"
    Width="[300.0F]"
    Height="[200.0F]" />
```

## Notes

- Windows only — requires Desktop PowerPoint
- Must be placed inside a `PowerPointApplicationScope`
- Position and size values are in points
- When position/size are not specified, the media inherits the placeholder's dimensions
- `Left` and `Top` must not be negative; `Width` and `Height` must not be less than 50
