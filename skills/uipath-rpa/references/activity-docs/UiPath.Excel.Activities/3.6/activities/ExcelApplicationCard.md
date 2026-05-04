# Use Excel File

`UiPath.Excel.Activities.Business.ExcelApplicationCard`

Opens an Excel workbook and provides a scope for child activities to interact with it. This is the primary container for all Windows Excel activities that operate on a workbook.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** None (this is a scope activity itself)

## Properties

### File
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `WorkbookPath` | Workbook path | InArgument | `string` | Yes | | The path to the Excel file. If the file does not exist and you select the CreateNewFile option, StudioX creates the file. |
| `Password` | Password | InArgument | `string` | No | `null` | The password required for opening the Excel workbook, if the file is password-protected. |
| `SecurePassword` | Secure password | InArgument | `SecureString` | No | `null` | Secure string variant of the open password. Cannot be set simultaneously with Password. |
| `EditPassword` | Edit password | InArgument | `string` | No | `null` | The password required for editing the Excel workbook, if the file is password-protected. |
| `SecureEditPassword` | Secure edit password | InArgument | `SecureString` | No | `null` | Secure string variant of the edit password. Cannot be set simultaneously with EditPassword. |

### Options
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `CreateNewFile` | Create if not exists | Property | `bool` | No | `True` | If the workbook cannot be found at the specified path, a new Excel workbook is created. When cleared, an error message is displayed if the workbook is not found. |
| `AutoSave` | Save changes | Property | `bool` | No | `True` | Saves the workbook after each Excel activity that makes a change to its content. Use the Save Excel File activity when disabled. |
| `ReadOnly` | Read-only | Property | `bool` | No | `False` | Opens the workbook in read-only mode. |
| `KeepExcelFileOpen` | Keep excel file open | Property | `bool` | No | `False` | Keeps the workbook open after running the project, instead of closing it. |
| `UseTemplate` | Use template | Property | `bool` | No | `False` | Enables template file support. When enabled, the TemplatePath property becomes visible. |
| `TemplatePath` | Template | InArgument | `string` | No | `null` | A file that represents the structure of a file that will only exist when the automation is run. Only visible when UseTemplate is True. |
| `ReadFormatting` | Read formatting | Property | `ReadFormattingOptions?` | No | `null` (Same as project) | Choose what formatting should be applied to values read from Excel. |
| `ResizeWindow` | Resize window | Property | `ResizeWindowOptions` | No | `None` | Resizes the Excel window accordingly. If Show Excel Window is set to false in the Project Settings, this property is ignored. |
| `SensitivityOperation` | Sensitivity operation | Property | `ExcelLabelOperation` | No | `None` | Sensitivity operation to be applied using the sensitivity label. |
| `SensitivityLabel` | Sensitivity label | InArgument | `object` | No | | String Id for the sensitivity label or an instance of IExcelLabelObject. Used only when the sensitivity operation is Add. |

### Designer
| Name | Display Name | Kind | Type | Required | Description |
|------|-------------|------|------|----------|-------------|
| `VariableName` | Reference as | NotMappedProperty | `string` | Yes | The name used to reference this workbook in child activities. |

## Conditional Visibility

- `TemplatePath` is only visible when `UseTemplate` is `True`.
- `Password` and `SecurePassword` are mutually exclusive (menu action toggles between them).
- `EditPassword` and `SecureEditPassword` are mutually exclusive (menu action toggles between them).
- `Visible` property is deprecated and hidden.
- `Body` property is hidden.

### Enum Reference

#### `ReadFormattingOptions`
| Value | Display Name |
|-------|-------------|
| `Default` | Default |
| `RawValue` | Raw value |
| `DisplayValue` | Display value |

#### `ResizeWindowOptions`
| Value | Display Name |
|-------|-------------|
| `None` | None |
| `Minimize` | Minimize |
| `Maximize` | Maximize |

#### `ExcelLabelOperation`
| Value | Display Name |
|-------|-------------|
| `None` | None |
| `Add` | Add |
| `Clear` | Clear |

## XAML Example
```xml
<excel:ExcelApplicationCard
  WorkbookPath="[filePath]"
  AutoSave="True"
  CreateNewFile="True"
  ReadOnly="False"
  DisplayName="Use Excel File">
  <excel:ExcelApplicationCard.Body>
    <ActivityAction x:TypeArguments="excel:IWorkbookQuickHandle">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="excel:IWorkbookQuickHandle" Name="Excel" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Do">
        <!-- child activities here -->
      </Sequence>
    </ActivityAction>
  </excel:ExcelApplicationCard.Body>
</excel:ExcelApplicationCard>
```

## Notes
- This activity acts as a scope (container) for other Excel activities. Most Windows Excel activities must be placed inside it.
- It is recommended to use this activity inside an `ExcelProcessScopeX` or `SequenceX` for better Excel process lifecycle management. A design-time warning is shown if not.
- When opening URLs (SharePoint), the file is opened in read-only mode and paths longer than 255 characters are rejected.
- The `CreateNewFile` option is not supported with URL-based paths.
