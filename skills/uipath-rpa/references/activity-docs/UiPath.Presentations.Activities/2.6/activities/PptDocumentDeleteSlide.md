# Delete Slide

`UiPath.Presentations.Activities.PptDocumentDeleteSlide`

Deletes a slide from a presentation. This activity can be used without Desktop PowerPoint installed and is faster than its Interop equivalent.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `SlideIndex` | Slide number | InArgument | `int` | Yes | | | Position of the slide to delete |
| `FilePath` | Presentation (local path) | InArgument | `string` | Conditional | | | Presentation to delete from |
| `PathResource` | Presentation | InArgument | `IResource` | Conditional | | | Presentation to delete from |

## Valid Configurations

This activity supports two file input modes (mutually exclusive via OverloadGroups):

**Mode A — Resource**: Set `PathResource` to an `IResource` handle.
**Mode B — Local Path**: Set `FilePath` to a local file path string.

## XAML Example

```xml
<pres:PptDocumentDeleteSlide
    DisplayName="Delete Slide"
    SlideIndex="[3]"
    FilePath="[&quot;C:\Presentations\demo.pptx&quot;]" />
```

## Notes

- Does not require Desktop PowerPoint to be installed (uses OpenXML SDK)
- Cross-platform: works on both Windows and Linux
