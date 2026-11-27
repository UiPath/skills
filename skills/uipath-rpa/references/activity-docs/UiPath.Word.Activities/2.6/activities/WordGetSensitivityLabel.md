# Get Word Sensitivity Label

`UiPath.Word.Activities.WordGetSensitivityLabel`

Retrieves the sensitivity label from the Word document opened in the parent scope.

**Package:** `UiPath.Word.Activities`
**Category:** Word
**Required Scope:** `WordApplicationScope`
**Platform:** Windows only

## Properties

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `SensitivityLabel` | Sensitivity label | `IWordLabelObject` | The sensitivity label retrieved from the document. Contains `LabelId` and `Justification` properties |

## XAML Example

```xml
<ui:WordGetSensitivityLabel
    DisplayName="Get Word Sensitivity Label"
    SensitivityLabel="[retrievedLabel]" />
```

## Notes

- Windows only — requires Microsoft Word installed
- Must be placed inside a Word Application Scope
- Returns `null` if no sensitivity label is applied to the document
- `IWordLabelObject` properties: `LabelId` (string), `Justification` (string)
