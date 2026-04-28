# Add Picture

`UiPath.Word.Activities.WordAddImage`

Adds a picture at a specified location in the Word document opened in the parent scope.

**Package:** `UiPath.Word.Activities`
**Category:** Word
**Required Scope:** `WordApplicationScope`
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ImagePath` | Picture to insert | InArgument | `string` | Yes | | The file path of the image to insert |
| `Text` | Text | InArgument | `string` | | | The text to search for when inserting relative to text. Visible only when `InsertRelativeTo` is `Text` |
| `Bookmark` | Bookmark | InArgument | `string` | | | The bookmark name for positioning. Visible only when `InsertRelativeTo` is `Bookmark` |
| `OccurrenceIndex` | OccurrenceIndex | InArgument | `int?` | | | The 1-based index of the specific occurrence. Visible only when `InsertRelativeTo` is `Text` and `Occurrence` is `Specific` |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `InsertRelativeTo` | Insert relative to | `InsertRelativeType` | `Document` | The location reference for image insertion |
| `Position` | Position | `Position` | `End` | Position relative to the reference point |
| `Occurrence` | Occurrence | `Occurrence` | `All` | Which occurrence of the text to target. Visible only when `InsertRelativeTo` is `Text` |

## Valid Configurations

**Mode A — Relative to Document** (default): Set `InsertRelativeTo` to `Document`. Use `Position` (`Start`/`End`). `Text`, `Bookmark`, `Occurrence`, `OccurrenceIndex` are hidden.

**Mode B — Relative to Text**: Set `InsertRelativeTo` to `Text`. Set `Text` to the reference text. Use `Position` (`Before`/`After`/`Replace`). Set `Occurrence` and optionally `OccurrenceIndex`.

**Mode C — Relative to Bookmark**: Set `InsertRelativeTo` to `Bookmark`. Set `Bookmark` to the bookmark name. Use `Position` (`Before`/`After`/`Replace`).

### Conditional Properties

- **`Text`** (`string`) — Only visible when `InsertRelativeTo` is `Text`. Required when visible.
- **`Bookmark`** (`string`) — Only visible when `InsertRelativeTo` is `Bookmark`. Required when visible.
- **`Occurrence`** — Only visible when `InsertRelativeTo` is `Text`. Required when visible.
- **`OccurrenceIndex`** (`int?`) — Only visible when `InsertRelativeTo` is `Text` and `Occurrence` is `Specific`. Required when visible and must be a 1-based index (>= 1); otherwise the activity throws at runtime.

### Enum Reference

**`InsertRelativeType`**: `Document`, `Text`, `Bookmark`

**`Position`**: `Start`, `End`, `Before`, `After`, `Replace`

**`Occurrence`**: `All`, `First`, `Last`, `Specific`

## XAML Example

```xml
<ui:WordAddImage
    DisplayName="Add Picture"
    ImagePath="[imagePath]" />
```

## Notes

- Windows only — requires Microsoft Word installed
- Must be placed inside a Word Application Scope
- By default, inserts the image at the end of the document; use `InsertRelativeTo`, `Position`, `Occurrence`, and `OccurrenceIndex` for custom placement
- For cross-platform scenarios (where Word is not available), use the `DocumentAddImage` activity
