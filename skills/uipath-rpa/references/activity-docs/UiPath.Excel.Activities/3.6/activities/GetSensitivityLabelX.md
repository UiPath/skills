# Get Excel Sensitivity Label

`UiPath.Excel.Activities.Business.GetSensitivityLabelX`

Retrieves the sensitivity label from an Excel file.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Workbook` | Workbook | InArgument | `IWorkbookQuickHandle` | Yes | | Workbook handle obtained from an `ExcelApplicationCard`. |

### Output
| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `SensitivityLabel` | Sensitivity label | `OutArgument<IExcelLabelObject>` | Instance of IExcelLabelObject where to store the sensitivity label. |

## XAML Example
```xml
<excel:GetSensitivityLabelX
  DisplayName="Get Excel Sensitivity Label"
  Workbook="[workbookHandle]"
  SensitivityLabel="[labelOutput]" />
```

## Notes
- The output `SensitivityLabel` contains an `IExcelLabelObject` with the label ID and justification.
- Returns `null` if no sensitivity label is applied to the workbook.
