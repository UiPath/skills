# Add Text to Slide

`UiPath.Presentations.Activities.PptDocumentAddTextToSlide`

Inserts text into a placeholder. This activity can be used without Desktop PowerPoint installed and is faster than its Interop equivalent.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `SlideIndex` | Slide number | InArgument | `int` | Yes | | | The index of the slide containing the desired text form |
| `ShapeName` | Content placeholder | InArgument | `string` | Yes | | | The name of the shape where to insert |
| `Text` | Text to add | InArgument | `string` | Yes | | | Text to insert |
| `FilePath` | Presentation (local path) | InArgument | `string` | Conditional | | | Presentation where to insert |
| `PathResource` | Presentation | InArgument | `IResource` | Conditional | | | Presentation where to insert |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ClearExistingText` | Clear existing text in content placeholder | `bool` | `false` | If true, clears the text in the content placeholder before adding the new text |

## Valid Configurations

This activity supports two file input modes (mutually exclusive via OverloadGroups):

**Mode A — Resource**: Set `PathResource` to an `IResource` handle from UiPath's storage system.
**Mode B — Local Path**: Set `FilePath` to a local file path string.

Properties `FilePath` and `PathResource` are mutually exclusive.

## XAML Example

```xml
<pres:PptDocumentAddTextToSlide
    DisplayName="Add Text to Slide"
    SlideIndex="[1]"
    ShapeName="[&quot;Title 1&quot;]"
    Text="[&quot;Hello World&quot;]"
    FilePath="[&quot;C:\Presentations\demo.pptx&quot;]"
    ClearExistingText="True" />
```

## Notes

- Does not require Desktop PowerPoint to be installed (uses OpenXML SDK)
- Cross-platform: works on both Windows and Linux
