# Format Slide Content

`UiPath.Presentations.Activities.FormatSlideContent`

Modifies formatting of slide content elements such as Z-index, font size, or shape name using the PowerPoint Interop API.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint.Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Presentation` | Presentation | InArgument | `IPresentationQuickHandle` | Yes | | | Presentation in which to modify content |
| `SlideIndex` | Slide number | InArgument | `int` | Yes | | | Slide number containing the content to update |
| `ShapeName` | Content to modify | InArgument | `string` | Yes | | | Name of the element to modify |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ModificationToAdd` | Modification type | `FormatSlideContentModificationType` | | The type of modification to apply. Used with the Add modification button |
| `AddModification` | Add modification | ActionButton | | Designer button to add the selected modification type |

### Enum Reference

**`FormatSlideContentModificationType`**: `ZIndex` (Bring to front / Send to back), `FontSize` (Set font size), `ChangeShapeName` (Change shape name)

## Child Activities (Modifications)

When the **Add modification** button is clicked in the designer, a child activity is added inside the `FormatSlideContent` scope based on the selected `ModificationToAdd` value. Each child activity represents a single formatting operation:

| ModificationType | Child Activity Class | Properties |
|-----------------|---------------------|------------|
| `ZIndex` | `ZIndexFormatSlideModification` | `Action` (`ZIndexChangeType`, required, default `BringToFront`) — the Z-order action to apply |
| `FontSize` | `FontSizeFormatSlideContentModification` | `FontSize` (InArgument `int`, required) — the font size to set |
| `ChangeShapeName` | `ChangeShapeNameSlideContentModification` | `NewShapeName` (InArgument `string`, required) — the new name to assign to the shape |

**`ZIndexChangeType`**: `BringToFront`, `SendToBack`

Multiple modifications can be stacked inside a single `FormatSlideContent` activity.

## XAML Example

```xml
<pres:FormatSlideContent
    DisplayName="Format Slide Content"
    Presentation="[presentation]"
    SlideIndex="[1]"
    ShapeName="[&quot;Title 1&quot;]">
    <pres:FontSizeFormatSlideContentModification
        DisplayName="Set font size"
        FontSize="[24]" />
    <pres:ZIndexFormatSlideModification
        DisplayName="Bring to front / Send to back"
        Action="BringToFront" />
    <pres:ChangeShapeNameSlideContentModification
        DisplayName="Change shape name"
        NewShapeName="[&quot;UpdatedTitle&quot;]" />
</pres:FormatSlideContent>
```

## Notes

- Windows only — requires Desktop PowerPoint
- Must be placed inside a `PowerPointApplicationScope`
- At least one child modification is required — the activity fails validation if no modifications are added
- Modifications are added via the designer's Add modification button; each modification type creates a child activity element in XAML
- Multiple modifications can be applied in a single `FormatSlideContent` invocation
