# Copy Paste Slide

`UiPath.Presentations.Activities.CopyPasteSlide`

Copies a slide from one presentation and pastes it to another position, optionally in a different presentation. Can also move slides.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint.Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `SourcePresentation` | Source presentation | InArgument | `IPresentationQuickHandle` | Yes | | | The presentation from which to copy the slide |
| `SlideToCopy` | The index of the slide to copy | InArgument | `int` | Yes | | | The index of the slide to copy |
| `DestinationPresentation` | Destination presentation | InArgument | `IPresentationQuickHandle` | Yes | | | The presentation to which the slide will be copied |
| `WhereToInsert` | Where to insert | InArgument | `int` | Yes | | | The index at which to insert the copied slide |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Move` | Move | `bool` | `false` | Whether to move (delete original) or copy the slide |

## XAML Example

```xml
<pres:CopyPasteSlide
    DisplayName="Copy Slide"
    SourcePresentation="[sourcePresentation]"
    SlideToCopy="[1]"
    DestinationPresentation="[destPresentation]"
    WhereToInsert="[3]"
    Move="False" />
```

## Notes

- Windows only — requires Desktop PowerPoint
- Source and destination presentations must both be open within `PowerPointApplicationScope` scopes
- Set `Move` to `true` to remove the slide from the source presentation after copying
