# Append Text

`UiPath.Word.Activities.DocumentAppendText`

Writes text at the end of a Word document.

**Package:** `UiPath.Word.Activities`
**Category:** Word

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FilePath` | File path | InArgument | `string` | Yes* | | The path to the Word document file |
| `PathResource` | File | InArgument | `IResource` | Yes* | | A file resource reference to the Word document |
| `Text` | Text | InArgument | `string` | Yes | | The text to append to the document |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `NewLine` | New line | `bool` | `true` | Whether to insert a new line before appending the text |

## Valid Configurations

This activity supports two input modes (mutually exclusive via OverloadGroups):

**Mode A — Local Path**: Set `FilePath` to the document path.
**Mode B — Resource**: Set `PathResource` to a file resource reference.

Only one of `FilePath` or `PathResource` should be set.

## XAML Example

```xml
<ui:DocumentAppendText
    DisplayName="Append Text"
    FilePath="[documentPath]"
    Text="[textToAppend]"
    NewLine="True" />
```

## Notes

- Cross-platform activity (works on both Windows and Linux)
