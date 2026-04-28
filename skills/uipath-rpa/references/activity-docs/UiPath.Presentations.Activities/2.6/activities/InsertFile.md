# Add File to Slide

`UiPath.Presentations.Activities.InsertFile`

Inserts a file from disk into a slide and displays it as an icon.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint.Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Presentation` | Presentation | InArgument | `IPresentationQuickHandle` | Yes | | | Presentation where to insert the file |
| `SlideIndex` | Slide number | InArgument | `int` | Yes | | | The index of the slide to insert into |
| `ShapeName` | Content placeholder | InArgument | `string` | | | | The name of the shape where to insert |
| `FilePath` | File to add | InArgument | `string` | Yes | | | The path to the file to insert |
| `IconLabel` | Icon label | InArgument | `string` | | | | Caption for the icon. Defaults to the file name |
| `NewShapeName` | New shape name | InArgument | `string` | | | | New name to assign to the shape |

## XAML Example

```xml
<pres:InsertFile
    DisplayName="Add File to Slide"
    Presentation="[presentation]"
    SlideIndex="[2]"
    FilePath="[&quot;C:\Documents\report.pdf&quot;]"
    IconLabel="[&quot;Q4 Report&quot;]" />
```

## Notes

- Windows only — requires Desktop PowerPoint
- Must be placed inside a `PowerPointApplicationScope`
- The file is embedded as an OLE object and displayed as an icon
- `ShapeName` is optional — if omitted, the file is inserted at a default position on the slide
