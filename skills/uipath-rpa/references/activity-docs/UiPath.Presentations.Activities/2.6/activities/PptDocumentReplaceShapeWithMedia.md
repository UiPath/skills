# Add Image/Video to Slide

`UiPath.Presentations.Activities.PptDocumentReplaceShapeWithMedia`

Replaces a placeholder shape with a media element (image or video). This activity can be used without Desktop PowerPoint installed and is faster than its Interop equivalent.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `SlideIndex` | Slide number | InArgument | `int` | Yes | | | The index of the slide on which to do the replacement |
| `ShapeName` | Shape Name | InArgument | `string` | Yes | | | The name of the shape to replace with media |
| `Media` | Image/Video file | InArgument | `string` | Yes | | | Absolute path to an existing media file (image or video) to use for replacement |
| `FilePath` | Presentation (local path) | InArgument | `string` | Conditional | | | Presentation where to insert |
| `PathResource` | Presentation | InArgument | `IResource` | Conditional | | | Presentation where to insert |
| `NewShapeName` | New Shape Name | InArgument | `string` | | | | The new name to assign to the shape |
| `Left` | Left | InArgument | `float?` | | | | How far right to move the item (points). Must not be negative |
| `Top` | Top | InArgument | `float?` | | | | How far down to move the item (points). Must not be negative |
| `Width` | Item width | InArgument | `float?` | | | | Width of the inserted item (points). Must not be less than 50 |
| `Height` | Item height | InArgument | `float?` | | | | Height of the inserted item (points). Must not be less than 50 |

## Valid Configurations

This activity supports two file input modes (mutually exclusive via OverloadGroups):

**Mode A — Resource**: Set `PathResource` to an `IResource` handle.
**Mode B — Local Path**: Set `FilePath` to a local file path string.

## XAML Example

```xml
<pres:PptDocumentReplaceShapeWithMedia
    DisplayName="Add Image to Slide"
    SlideIndex="[1]"
    ShapeName="[&quot;Picture Placeholder&quot;]"
    Media="[&quot;C:\Images\logo.png&quot;]"
    FilePath="[&quot;C:\Presentations\demo.pptx&quot;]"
    Width="[200.0F]"
    Height="[150.0F]" />
```

## Notes

- Does not require Desktop PowerPoint to be installed (uses OpenXML SDK)
- Cross-platform: works on both Windows and Linux
- Position and size values are in points
- When position/size values are not specified, the media inherits the placeholder's dimensions
- `Left` and `Top` must not be negative; `Width` and `Height` must not be less than 50
