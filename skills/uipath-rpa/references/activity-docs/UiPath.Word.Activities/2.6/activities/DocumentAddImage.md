# Add Picture

`UiPath.Word.Activities.DocumentAddImage`

Adds an image to a Word document at a specified location relative to the document, a text match, or a bookmark.

**Package:** `UiPath.Word.Activities`
**Category:** Word

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FilePath` | File path | InArgument | `string` | Yes* | | The path to the Word document file |
| `PathResource` | File | InArgument | `IResource` | Yes* | | A file resource reference to the Word document |
| `ImagePath` | Picture to insert | InArgument | `string` | Yes | | The file path of the image to insert |
| `Text` | Text | InArgument | `string` | | | The text to search for when inserting relative to text. Visible only when `InsertRelativeTo` is `Text` |
| `Bookmark` | Bookmark | InArgument | `string` | | | The bookmark name for positioning. Visible only when `InsertRelativeTo` is `Bookmark` |
| `OccurrenceIndex` | OccurrenceIndex | InArgument | `int?` | | | The 1-based index of the specific occurrence. Visible only when `InsertRelativeTo` is `Text` and `Occurrence` is `Specific` |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `InsertRelativeTo` | Insert Relative To | `InsertRelativeType` | `Document` | Determines the reference point for image insertion |
| `Position` | Position | `Position` | `End` | Position relative to the reference point |
| `Occurrence` | Occurrence | `Occurrence` | `All` | Which occurrence of the search text to target. Visible only when `InsertRelativeTo` is `Text` |

## Valid Configurations

This activity supports three insertion modes based on `InsertRelativeTo`:

**Mode A — Relative to Document** (default): Set `InsertRelativeTo` to `Document`. Use `Position` (`Start` or `End`). The conditional properties (`Text`, `Bookmark`, `Occurrence`, `OccurrenceIndex`) are hidden; `FilePath`/`PathResource` and `ImagePath` remain visible.

**Mode B — Relative to Text**: Set `InsertRelativeTo` to `Text`. Set `Text` to the search string. Use `Position` (`Before`/`After`/`Replace`). Set `Occurrence` and optionally `OccurrenceIndex`.

**Mode C — Relative to Bookmark**: Set `InsertRelativeTo` to `Bookmark`. Set `Bookmark` to the bookmark name. Use `Position` (`Before`/`After`/`Replace`).

Additionally, `FilePath` and `PathResource` are mutually exclusive (OverloadGroups).

### Conditional Properties

- **`Text`** (`string`) — Only visible when `InsertRelativeTo` is `Text`. Required when visible (null or whitespace throws at runtime).
- **`Bookmark`** (`string`) — Only visible when `InsertRelativeTo` is `Bookmark`. Required when visible (null or whitespace throws at runtime).
- **`Occurrence`** (`Occurrence`) — Only visible when `InsertRelativeTo` is `Text`. Required when visible.
- **`OccurrenceIndex`** (`int?`) — Only visible when `InsertRelativeTo` is `Text` AND `Occurrence` is `Specific`. Required when visible and must be a 1-based index (>= 1); otherwise the activity throws at runtime.

### Enum Reference

**`InsertRelativeType`**: `Document`, `Bookmark`, `Text`

**`Position`**: `Start`, `End`, `Before`, `After`, `Replace`

**`Occurrence`**: `All`, `First`, `Last`, `Specific`

## XAML Example

**Insert at end of document:**
```xml
<ui:DocumentAddImage
    DisplayName="Add Picture"
    FilePath="[documentPath]"
    ImagePath="[imagePath]"
    InsertRelativeTo="Document"
    Position="End" />
```

**Insert after specific text occurrence:**
```xml
<ui:DocumentAddImage
    DisplayName="Add Picture"
    FilePath="[documentPath]"
    ImagePath="[imagePath]"
    InsertRelativeTo="Text"
    Text="[&quot;Figure 1&quot;]"
    Occurrence="First"
    Position="After" />
```

## Notes

- Cross-platform activity (works on both Windows and Linux)
