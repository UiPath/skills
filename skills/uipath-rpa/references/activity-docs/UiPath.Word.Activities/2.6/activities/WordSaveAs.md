# Save Document As

`UiPath.Word.Activities.WordSaveAs`

Saves the Word document opened in the parent scope as a different file, optionally in a different format.

**Package:** `UiPath.Word.Activities`
**Category:** Word
**Required Scope:** `WordApplicationScope`
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FilePath` | Save as file | InArgument | `string` | Yes | | The file path to save the document to |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `SaveAsFileType` | Save as type | `WordSaveAsType` | `XmlDocument` | The file format to save as |
| `ReplaceExisting` | Replace existing | `bool` | `true` | Whether to overwrite an existing file at the target path |

### Enum Reference

**`WordSaveAsType`**: `XmlDocument` (.docx), `MacroEnabledDocument` (.docm), `OldDocument` (.doc), `WebPage` (.html), `FilteredWebPage` (filtered .html), `RichText` (.rtf), `PlainText` (.txt)

## XAML Example

```xml
<ui:WordSaveAs
    DisplayName="Save Document As"
    FilePath="[outputPath]"
    SaveAsFileType="XmlDocument"
    ReplaceExisting="True" />
```

## Notes

- Windows only — requires Microsoft Word installed
- Must be placed inside a Word Application Scope
