# Add New Slide

`UiPath.Presentations.Activities.InsertSlide`

Inserts a new slide into a presentation using the PowerPoint Interop API.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint.Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Presentation` | Presentation | InArgument | `IPresentationQuickHandle` | Yes | | | Presentation where to insert the slide |
| `SlideMasterName` | Slide Master | InArgument | `string` | Yes | `"(default)"` | | The name of the Slide Master containing the desired layout. When set to `"(default)"`, the first available slide master is used automatically |
| `LayoutName` | Layout | InArgument | `string` | Yes | | | The name of the layout |
| `InsertPosition` | Insert position | InArgument | `int` | | | | Position at which to insert the new slide (visible only when `InsertType` is `SpecifiedIndex`) |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `InsertType` | Add as | `InsertPositionType` | `End` | Position where to insert: Beginning, End, or a specific index |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `InsertedAtPosition` | Save new slide number as | `int` | The index at which the slide was inserted |

### Conditional Properties

- **`InsertPosition`** (`int`) — Only visible when `InsertType` is `SpecifiedIndex`. Hidden when `InsertType` is `Beginning` or `End`.

### Enum Reference

**`InsertPositionType`**: `SpecifiedIndex` (At specified index), `Beginning` (At start), `End` (At end)

## XAML Example

```xml
<pres:InsertSlide
    DisplayName="Add New Slide"
    Presentation="[presentation]"
    SlideMasterName="[&quot;(default)&quot;]"
    LayoutName="[&quot;Title and Content&quot;]"
    InsertType="End"
    InsertedAtPosition="[newSlideIndex]" />
```

## Notes

- Windows only — requires Desktop PowerPoint
- Must be placed inside a `PowerPointApplicationScope`
- `InsertPosition` is only shown when `InsertType` is `SpecifiedIndex`
