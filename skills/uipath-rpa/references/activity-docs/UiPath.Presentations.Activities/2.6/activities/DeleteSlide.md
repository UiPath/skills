# Delete Slide

`UiPath.Presentations.Activities.DeleteSlide`

Deletes a slide from a presentation using the PowerPoint Interop API.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint.Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Presentation` | Presentation | InArgument | `IPresentationQuickHandle` | Yes | | | Presentation from which to delete the slide |
| `DeletePosition` | Slide number | InArgument | `int` | Yes | | | Position of the slide to delete |

## XAML Example

```xml
<pres:DeleteSlide
    DisplayName="Delete Slide"
    Presentation="[presentation]"
    DeletePosition="[3]" />
```

## Notes

- Windows only — requires Desktop PowerPoint
- Must be placed inside a `PowerPointApplicationScope`
