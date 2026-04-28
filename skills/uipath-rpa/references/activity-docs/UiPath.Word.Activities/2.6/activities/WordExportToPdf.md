# Save Document as PDF

`UiPath.Word.Activities.WordExportToPdf`

Exports the Word document opened in the parent scope to a PDF file.

**Package:** `UiPath.Word.Activities`
**Category:** Word
**Required Scope:** `WordApplicationScope`
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FilePath` | File path | InArgument | `string` | Yes | | The output PDF file path |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ReplaceExisting` | Replace existing | `bool` | `true` | Whether to overwrite an existing PDF file at the target path |

## XAML Example

```xml
<ui:WordExportToPdf
    DisplayName="Save Document as PDF"
    FilePath="[pdfOutputPath]"
    ReplaceExisting="True" />
```

## Notes

- Windows only — requires Microsoft Word installed
- Must be placed inside a Word Application Scope
- Uses Word's native PDF export functionality
