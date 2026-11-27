# Add New Slide

`UiPath.Presentations.Activities.PptDocumentInsertSlide`

Inserts a new slide into a presentation. This activity can be used without Desktop PowerPoint installed and is faster than its Interop equivalent.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `SlideMasterName` | Slide Master | InArgument | `string` | Yes | `"(default)"` | | The name of the Slide Master containing the desired layout. When set to `"(default)"`, the first available slide master is used automatically |
| `LayoutName` | Layout | InArgument | `string` | Yes | | | The name of the layout |
| `InsertPosition` | Insert position | InArgument | `int` | | | | Position at which to insert the new slide (visible only when `InsertType` is `SpecifiedIndex`) |
| `FilePath` | Presentation (local path) | InArgument | `string` | Conditional | | | Presentation where to insert |
| `PathResource` | Presentation | InArgument | `IResource` | Conditional | | | Presentation where to insert |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `InsertType` | Add as | `InsertPositionType` | `End` | Position where to insert: Beginning, End, or a specific index |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `InsertedAtPosition` | Save new slide number as | `int` | The index at which the slide was inserted |

## Valid Configurations

This activity supports two file input modes (mutually exclusive via OverloadGroups):

**Mode A — Resource**: Set `PathResource` to an `IResource` handle.
**Mode B — Local Path**: Set `FilePath` to a local file path string.

### Conditional Properties

- **`InsertPosition`** (`int`) — Only visible when `InsertType` is `SpecifiedIndex`. Hidden when `InsertType` is `Beginning` or `End`.

### Enum Reference

**`InsertPositionType`**: `SpecifiedIndex` (At specified index), `Beginning` (At start), `End` (At end)

## XAML Example

**Insert at end (default):**
```xml
<pres:PptDocumentInsertSlide
    DisplayName="Add New Slide"
    SlideMasterName="[&quot;(default)&quot;]"
    LayoutName="[&quot;Title and Content&quot;]"
    InsertType="End"
    FilePath="[&quot;C:\Presentations\demo.pptx&quot;]"
    InsertedAtPosition="[newSlideIndex]" />
```

**Insert at specific position:**
```xml
<pres:PptDocumentInsertSlide
    DisplayName="Add New Slide at Position"
    SlideMasterName="[&quot;(default)&quot;]"
    LayoutName="[&quot;Blank&quot;]"
    InsertType="SpecifiedIndex"
    InsertPosition="[2]"
    FilePath="[&quot;C:\Presentations\demo.pptx&quot;]"
    InsertedAtPosition="[newSlideIndex]" />
```

## Notes

- Does not require Desktop PowerPoint to be installed (uses OpenXML SDK)
- Cross-platform: works on both Windows and Linux
