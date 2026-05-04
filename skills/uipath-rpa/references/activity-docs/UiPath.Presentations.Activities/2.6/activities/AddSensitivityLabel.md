# Add Sensitivity Label

`UiPath.Presentations.Activities.AddSensitivityLabel`

Adds a sensitivity label to a PowerPoint document.

**Package:** `UiPath.Presentations.Activities`
**Category:** PowerPoint.Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Presentation` | Presentation | InArgument | `IPresentationQuickHandle` | Yes | | | The presentation to which to add the sensitivity label |
| `SensitivityLabel` | Sensitivity label | InArgument | `object` | Yes | | | String ID or an `IPptLabelObject` instance to add to the file |
| `Justification` | Justification | InArgument | `string` | | | | Justification to use when applying the label |

## XAML Example

```xml
<pres:AddSensitivityLabel
    DisplayName="Add Sensitivity Label"
    Presentation="[presentation]"
    SensitivityLabel="[&quot;label-guid-here&quot;]"
    Justification="[&quot;Business requirement&quot;]" />
```

## Notes

- Windows only — requires Desktop PowerPoint
- Must be placed inside a `PowerPointApplicationScope`
- `SensitivityLabel` can be either a string label ID or an `IPptLabelObject` instance from `GetSensitivityLabel`
