# Add Hyperlink to Document

`UiPath.Word.Activities.DocumentInsertHyperlink`

Adds a hyperlink to a Word document at a specified location.

**Package:** `UiPath.Word.Activities`
**Category:** Word

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FilePath` | File path | InArgument | `string` | Yes* | | The path to the Word document file |
| `PathResource` | File | InArgument | `IResource` | Yes* | | A file resource reference to the Word document |
| `TextToDisplay` | Text to display | InArgument | `string` | Yes | | The visible text of the hyperlink |
| `Address` | Address | InArgument | `string` | Yes | | The URL or address the hyperlink points to |
| `TextToSearchFor` | Text to search for | InArgument | `string` | | | The text to find in the document for positioning. Visible only when `InsertRelativeTo` is `Text` |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `InsertRelativeTo` | Insert relative to | `InsertHyperlinkRelativeToType` | `Document` | The location reference for hyperlink insertion |
| `Position` | Position where to insert | `Position` | `End` | Position relative to the reference point |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Result` | Found | `bool` | Indicates whether the hyperlink was successfully inserted |

## Valid Configurations

This activity supports two insertion modes based on `InsertRelativeTo`:

**Mode A — Relative to Document** (default): Set `InsertRelativeTo` to `Document`. `TextToSearchFor` is hidden.

- Supported `Position` values: `Start`, `End`
- Using `Before`, `After`, or `Replace` with this mode will silently fail (returns `false`).

**Mode B — Relative to Text**: Set `InsertRelativeTo` to `Text`. Set `TextToSearchFor` to locate the reference text.

- Supported `Position` values: `Before`, `After`, `Replace`
- Using `Start` or `End` with this mode will silently fail (returns `false`).

Additionally, `FilePath` and `PathResource` are mutually exclusive (OverloadGroups).

### Conditional Properties

- **`TextToSearchFor`** (`string`) — Only visible when `InsertRelativeTo` is `Text`. Required when visible.

### Enum Reference

**`InsertHyperlinkRelativeToType`**: `Document`, `Text`

**`Position`**: `Start`, `End`, `Before`, `After`, `Replace`

## XAML Example

**Insert at end of document:**
```xml
<ui:DocumentInsertHyperlink
    DisplayName="Add Hyperlink to Document"
    FilePath="[documentPath]"
    TextToDisplay="[&quot;Click here&quot;]"
    Address="[&quot;https://example.com&quot;]"
    InsertRelativeTo="Document"
    Position="End"
    Result="[insertResult]" />
```

**Insert after specific text:**
```xml
<ui:DocumentInsertHyperlink
    DisplayName="Add Hyperlink to Document"
    FilePath="[documentPath]"
    TextToDisplay="[&quot;Learn more&quot;]"
    Address="[&quot;https://example.com&quot;]"
    InsertRelativeTo="Text"
    TextToSearchFor="[&quot;For details&quot;]"
    Position="After"
    Result="[insertResult]" />
```

## Notes

- Cross-platform activity (works on both Windows and Linux)
