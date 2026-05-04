# Append Text

`UiPath.Word.Activities.WordAppendText`

Appends text to the end of the Word document, optionally inserting a new line before the text.

**Package:** `UiPath.Word.Activities`
**Category:** Word
**Required Scope:** `WordApplicationScope`
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Text` | Text | InArgument | `string` | Yes | | The text to append to the document |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `NewLine` | New line | `bool` | `true` | Whether to insert a new line before appending the text |

## XAML Example

```xml
<ui:WordAppendText
    DisplayName="Append Text"
    Text="[textToAppend]"
    NewLine="True" />
```

## Notes

- Windows only — requires Microsoft Word installed
- Must be placed inside a Word Application Scope
