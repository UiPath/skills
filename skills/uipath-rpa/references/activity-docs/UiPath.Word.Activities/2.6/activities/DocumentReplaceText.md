# Replace Text

`UiPath.Word.Activities.DocumentReplaceText`

Replaces all occurrences of a specified text within a Word document with another text.

**Package:** `UiPath.Word.Activities`
**Category:** Word

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FilePath` | File path | InArgument | `string` | Yes* | | The path to the Word document file |
| `PathResource` | File | InArgument | `IResource` | Yes* | | A file resource reference to the Word document |
| `Search` | Search | InArgument | `string` | Yes | | The text to search for in the document |
| `Replace` | Replace | InArgument | `string` | Yes | | The replacement text |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Found` | Found | `bool` | Indicates whether the search text was found and replaced |

## Valid Configurations

This activity supports two input modes (mutually exclusive via OverloadGroups):

**Mode A — Local Path**: Set `FilePath` to the document path.
**Mode B — Resource**: Set `PathResource` to a file resource reference.

Only one of `FilePath` or `PathResource` should be set.

## XAML Example

```xml
<ui:DocumentReplaceText
    DisplayName="Replace Text"
    FilePath="[documentPath]"
    Search="[searchText]"
    Replace="[replaceText]"
    Found="[wasFound]" />
```

## Notes

- Cross-platform activity (works on both Windows and Linux)
