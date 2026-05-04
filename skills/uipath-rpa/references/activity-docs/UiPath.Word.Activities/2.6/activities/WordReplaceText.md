# Replace Text

`UiPath.Word.Activities.WordReplaceText`

Replaces all occurrences of a text within the Word document with another text.

**Package:** `UiPath.Word.Activities`
**Category:** Word
**Required Scope:** `WordApplicationScope`
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Search` | Search | InArgument | `string` | Yes | | The text to search for |
| `Replace` | Replace | InArgument | `string` | Yes | | The replacement text |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ReplaceAll` | Replace all | `bool` | `true` | If true, replaces all occurrences; otherwise only the first |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Found` | Found | `bool` | Indicates whether the search text was found |

## XAML Example

```xml
<ui:WordReplaceText
    DisplayName="Replace Text"
    Search="[searchText]"
    Replace="[replaceText]"
    ReplaceAll="True"
    Found="[wasFound]" />
```

## Notes

- Windows only — requires Microsoft Word installed
- Must be placed inside a Word Application Scope
