# Format Slide Content

`UiPath.Presentations.Activities.PptDocumentFormatSlideContent`

Modifies formatting of slide content elements such as Z-order, font size, or shape name. This activity can be used without Desktop PowerPoint installed.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `SlideNumber` | Slide number | InArgument | `int` | Yes | | | Slide number containing the content to update |
| `ContentToModify` | Content to modify | InArgument | `string` | Yes | | | Name of the element to modify |
| `PathResource` | Presentation | InArgument | `IResource` | Conditional | | | Presentation to modify/format |
| `Presentation` | Presentation (local path) | InArgument | `string` | Conditional | | | Presentation to modify/format |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ModificationToAdd` | Modification type | `PptDocumentSlideContentModificationType` | | The type of modification to apply. Used with the Add modification button to queue modifications |
| `AddModification` | Add modification | ActionButton | | Designer button to add the selected modification type to the activity |

## Valid Configurations

This activity supports two file input modes (mutually exclusive via OverloadGroups):

**Mode A — Resource**: Set `PathResource` to an `IResource` handle.
**Mode B — Local Path**: Set `Presentation` to a local file path string.

### Enum Reference

**`PptDocumentSlideContentModificationType`**: `ZOrder` (Change Z-order/layering), `FontSize` (Change font size), `ChangeShapeName` (Rename the shape)

## XAML Example

```xml
<pres:PptDocumentFormatSlideContent
    DisplayName="Format Slide Content"
    SlideNumber="[1]"
    ContentToModify="[&quot;Title 1&quot;]"
    PathResource="[presentationResource]">
    <pres:ShapeFontSizeSlideContentModification
        DisplayName="Set font size"
        FontSize="[24]" />
    <pres:ShapeZOrderSlideContentModification
        DisplayName="Bring to front / Send to back"
        Action="BringToFront" />
    <pres:ShapeChangeNameSlideContentModification
        DisplayName="Change shape name"
        NewShapeName="[&quot;UpdatedTitle&quot;]" />
</pres:PptDocumentFormatSlideContent>
```

## Notes

- Does not require Desktop PowerPoint to be installed (uses OpenXML SDK)
- Cross-platform: works on both Windows and Linux
- At least one child modification is required — the activity fails validation if no modifications are added
- Modifications are added via the designer's Add modification button; each modification type creates a child element in XAML
