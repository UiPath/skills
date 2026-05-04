# Read Text

`UiPath.Word.Activities.DocumentReadText`

Reads all text content from a Word document.

**Package:** `UiPath.Word.Activities`
**Category:** Word

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FilePath` | File path | InArgument | `string` | Yes* | | The path to the Word document file |
| `PathResource` | File | InArgument | `IResource` | Yes* | | A file resource reference to the Word document |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Text` | Text | `string` | The full text content extracted from the document |

## Valid Configurations

This activity supports two input modes (mutually exclusive via OverloadGroups):

**Mode A — Local Path**: Set `FilePath` to the document path.
**Mode B — Resource**: Set `PathResource` to a file resource reference.

Only one of `FilePath` or `PathResource` should be set.

## XAML Example

```xml
<ui:DocumentReadText
    DisplayName="Read Text"
    FilePath="[documentPath]"
    Text="[extractedText]" />
```

## Notes

- Cross-platform activity (works on both Windows and Linux)
- Reads document content directly without requiring Microsoft Word installed
