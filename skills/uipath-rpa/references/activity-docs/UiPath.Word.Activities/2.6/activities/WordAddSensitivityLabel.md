# Add or Update Word Sensitivity Label

`UiPath.Word.Activities.WordAddSensitivityLabel`

Adds or updates a sensitivity label on the Word document opened in the parent scope.

**Package:** `UiPath.Word.Activities`
**Category:** Word
**Required Scope:** `WordApplicationScope`
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `SensitivityLabel` | Sensitivity label | InArgument | `object` | Yes | | A sensitivity label ID (string) or an `IWordLabelObject` instance |
| `Justification` | Justification | InArgument | `string` | | | Justification text for applying or changing the label |

## XAML Example

```xml
<ui:WordAddSensitivityLabel
    DisplayName="Add or Update Word Sensitivity Label"
    SensitivityLabel="[sensitivityLabelId]"
    Justification="[&quot;Business requirement&quot;]" />
```

## Notes

- Windows only — requires Microsoft Word installed
- Must be placed inside a Word Application Scope
- Requires Microsoft Information Protection (MIP) to be configured
- `IWordLabelObject` has properties: `LabelId` (string) and `Justification` (string)
