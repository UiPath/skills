# Get Sensitivity Label

`UiPath.Presentations.Activities.GetSensitivityLabel`

Retrieves the sensitivity label from a PowerPoint file.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint.Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Presentation` | Presentation | InArgument | `IPresentationQuickHandle` | Yes | | | The presentation from which to retrieve the sensitivity label |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `SensitivityLabel` | Sensitivity Label | `IPptLabelObject` | The sensitivity label retrieved from the presentation |

## XAML Example

```xml
<pres:GetSensitivityLabel
    DisplayName="Get Sensitivity Label"
    Presentation="[presentation]"
    SensitivityLabel="[labelResult]" />
```

## Notes

- Windows only — requires Desktop PowerPoint
- Must be placed inside a `PowerPointApplicationScope`
- Returns an `IPptLabelObject` with `LabelId` and `Justification` properties
