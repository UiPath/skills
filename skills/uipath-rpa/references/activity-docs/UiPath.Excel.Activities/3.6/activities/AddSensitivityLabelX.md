# Add or Update Excel Sensitivity Label

`UiPath.Excel.Activities.Business.AddSensitivityLabelX`

Adds a sensitivity label to an Excel file.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Workbook` | Workbook | InArgument | `IWorkbookQuickHandle` | Yes | | Workbook handle obtained from an `ExcelApplicationCard`. |
| `SensitivityLabel` | Sensitivity label | InArgument | `object` | Yes | | String Id for the sensitivity label or an instance of IExcelLabelObject |
| `Justification` | Justification | InArgument | `string` | No | | Justification to use when applying the label |

## XAML Example
```xml
<excel:AddSensitivityLabelX
  DisplayName="Add or Update Excel Sensitivity Label"
  Workbook="[workbookHandle]"
  SensitivityLabel="[labelIdOrObject]"
  Justification="[&quot;Business requirement&quot;]" />
```

## Notes
- The `SensitivityLabel` property accepts either a string label ID or an `IExcelLabelObject` instance.
- The `Justification` property is optional and is used when applying or changing the label.
- If both a justification is set on the `IExcelLabelObject` and in the `Justification` property, the `Justification` property value takes precedence.
