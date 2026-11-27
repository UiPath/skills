# Paste Chart/Picture into Document

`UiPath.Word.Activities.WordPasteFromClipboard`

Pastes content from the clipboard into the Word document at a specified position. Commonly used with "Copy Excel Chart to Clipboard" to embed Excel charts in Word documents.

**Package:** `UiPath.Word.Activities`
**Category:** Word
**Required Scope:** `WordApplicationScope`
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Text` | Text | InArgument | `string` | | | The text to search for when pasting relative to text |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `PasteOption` | Paste option | `PasteOptionType` | `Picture` | How the clipboard content is pasted |
| `PasteRelativeTo` | Paste relative to | `PasteRelativeToType` | `Document` | The location reference for pasting |
| `Position` | Position where to paste | `Position` | `End` | Position relative to the reference point |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Found` | Found | `bool` | Indicates whether the reference text was found (when pasting relative to text) |

## Valid Configurations

**Mode A — Relative to Document** (default): Set `PasteRelativeTo` to `Document`. The `Text` property is not used.

- Supported `Position` values: `Start`, `End`
- Using `Before`, `After`, or `Replace` with this mode will throw an error.

**Mode B — Relative to Text**: Set `PasteRelativeTo` to `Text`. The `Text` property **must** be provided.

- Supported `Position` values: `Before`, `After`, `Replace`
- Using `Start` or `End` with this mode is not supported.

### Conditional Properties

- **`Text`** (`string`) — Only required when `PasteRelativeTo` is `Text`. Specifies the anchor text for positioning.

### Enum Reference

**`PasteOptionType`**: `EmbedData` (embeds a copy of the data), `LinkData` (links to the source data), `Picture` (pastes as a static image)

**`PasteRelativeToType`**: `Document`, `Text`

**`Position`**: `Start`, `End`, `Before`, `After`, `Replace`

## XAML Example

```xml
<ui:WordPasteFromClipboard
    DisplayName="Paste Chart/Picture into Document"
    PasteOption="Picture"
    PasteRelativeTo="Document"
    Position="End" />
```

## Notes

- Windows only — requires Microsoft Word installed
- Must be placed inside a Word Application Scope
- Typically used after copying an Excel chart to the clipboard
- When `PasteRelativeTo` is `Text`, set the `Text` property to locate the insertion point
