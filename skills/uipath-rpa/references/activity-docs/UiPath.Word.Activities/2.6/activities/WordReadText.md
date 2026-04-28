# Read Text

`UiPath.Word.Activities.WordReadText`

Reads all text from the Word document opened in the parent Word Application Scope.

**Package:** `UiPath.Word.Activities`
**Category:** Word
**Required Scope:** `WordApplicationScope`
**Platform:** Windows only

## Properties

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Text` | Text | `string` | The full text content of the document |

## XAML Example

```xml
<ui:WordApplicationScope DisplayName="Word Application Scope" FilePath="[documentPath]">
    <ui:WordApplicationScope.Body>
        <ActivityAction x:TypeArguments="x:Object">
            <ui:WordReadText
                DisplayName="Read Text"
                Text="[extractedText]" />
        </ActivityAction>
    </ui:WordApplicationScope.Body>
</ui:WordApplicationScope>
```

## Notes

- Windows only — requires Microsoft Word installed
- Must be placed inside a Word Application Scope
