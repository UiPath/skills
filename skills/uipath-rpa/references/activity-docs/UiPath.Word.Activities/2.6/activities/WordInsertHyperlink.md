# Add Hyperlink to Document

`UiPath.Word.Activities.WordInsertHyperlink`

Adds a hyperlink to the Word document at a specified location.

**Package:** `UiPath.Word.Activities`
**Category:** Word
**Required Scope:** `WordApplicationScope`
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `TextToDisplay` | Text to display | InArgument | `string` | Yes | | The visible text of the hyperlink |
| `Address` | Address | InArgument | `string` | Yes | | The URL or address the hyperlink points to |
| `TextToSearchFor` | Text to search for | InArgument | `string` | | | The text to find in the document for positioning. Only visible when `InsertRelativeTo` is `Text` |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `InsertRelativeTo` | Insert relative to | `InsertHyperlinkRelativeToType` | `Document` | The location reference for hyperlink insertion |
| `Position` | Position where to insert | `Position` | `End` | Position relative to the reference point |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Found` | Found | `bool` | Indicates whether the reference text was found (when inserting relative to text) |

## Valid Configurations

**Mode A — Relative to Document** (default): Set `InsertRelativeTo` to `Document`. `TextToSearchFor` is hidden.

- Supported `Position` values: `Start`, `End`
- Using `Before`, `After`, or `Replace` with this mode will throw an error.

**Mode B — Relative to Text**: Set `InsertRelativeTo` to `Text`. Set `TextToSearchFor` to the reference text.

- Supported `Position` values: `Before`, `After`, `Replace`
- Using `Start` or `End` with this mode is not supported.

### Conditional Properties

- **`TextToSearchFor`** (`string`) — Only visible when `InsertRelativeTo` is `Text`. Required when visible (throws if missing or empty).

### Enum Reference

**`InsertHyperlinkRelativeToType`**: `Document`, `Text`

**`Position`**: `Start`, `End`, `Before`, `After`, `Replace`

## XAML Example

**Insert at end of document:**
```xml
<ui:WordInsertHyperlink
    DisplayName="Add Hyperlink to Document"
    TextToDisplay="[&quot;Visit website&quot;]"
    Address="[&quot;https://example.com&quot;]"
    InsertRelativeTo="Document"
    Position="End"
    Found="[wasFound]" />
```

## Notes

- Windows only — requires Microsoft Word installed
- Must be placed inside a Word Application Scope
