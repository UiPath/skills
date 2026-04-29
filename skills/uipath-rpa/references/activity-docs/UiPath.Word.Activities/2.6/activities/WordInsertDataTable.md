# Insert DataTable in Document

`UiPath.Word.Activities.WordInsertDataTable`

Inserts a DataTable as a table in the Word document. Supports positional insertion relative to text or a bookmark.

**Package:** `UiPath.Word.Activities`
**Category:** Word
**Required Scope:** `WordApplicationScope`
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `DataTable` | DataTable | InArgument | `DataTable` | Yes | | The DataTable to insert as a table |
| `Text` | Text | InArgument | `string` | | | The text to search for when inserting relative to text. Visible only when `InsertRelativeTo` is `Text` |
| `Bookmark` | Bookmark | InArgument | `string` | | | The bookmark name for positioning. Visible only when `InsertRelativeTo` is `Bookmark` |
| `OccurrenceIndex` | OccurrenceIndex | InArgument | `int?` | | | The 1-based index of the specific occurrence. Visible only when `InsertRelativeTo` is `Text` and `Occurrence` is `Specific` |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `InsertRelativeTo` | Insert relative to | `InsertRelativeType` | `Document` | The location reference for table insertion |
| `Position` | Position | `Position` | `Start` | Position relative to the reference point |
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
<ui:WordInsertDataTable
    DisplayName="Insert DataTable in Document"
    DataTable="[myDataTable]"
    InsertRelativeTo="Document"
    Position="Start" />
```

## Notes

- Windows only — requires Microsoft Word installed
- Must be placed inside a Word Application Scope
- DataTable column headers are used as the table header row
