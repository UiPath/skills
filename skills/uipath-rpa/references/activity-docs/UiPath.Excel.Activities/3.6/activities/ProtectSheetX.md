# Protect Sheet

`UiPath.Excel.Activities.Business.ProtectSheetX`

Protects a sheet in an Excel workbook.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Sheet` | Sheet | InArgument | `ISheetRef` | Yes | | Choose sheet to protect. |
| `Password` | Password | InArgument | `string` | Conditional | | Password to protect the sheet. |
| `SecurePassword` | Password (SecureString) | InArgument | `SecureString` | Conditional | | Password to protect the sheet as a SecureString type. |

### Configuration
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `AdditionalPermissions` | Additional permissions | `ProtectSheetAdditionalPermissions` | `None` | Grant users of the sheet additional capabilities. |

### Enum Reference

#### `ProtectSheetAdditionalPermissions`
| Value | Description |
|-------|-------------|
| `None` | No additional permissions |
| `AllowDeletingColumns` | Allow deleting columns |
| `AllowDeletingRows` | Allow deleting rows |
| `DrawingObjects` | Drawing objects |
| `Scenarios` | Scenarios |
| `AllowFiltering` | Allow filtering |
| `AllowFormattingCells` | Allow formatting cells |
| `AllowFormattingColumns` | Allow formatting columns |
| `AllowFormattingRows` | Allow formatting rows |
| `AllowInsertingColumns` | Allow inserting columns |
| `AllowInsertingHyperlinks` | Allow inserting hyperlinks |
| `AllowInsertingRows` | Allow inserting rows |
| `AllowSorting` | Allow sorting |
| `AllowUsingPivotTables` | Allow using pivot tables |

## XAML Example
```xml
<excel:ProtectSheetX
  DisplayName="Protect Sheet"
  Sheet="[sheetReference]"
  Password="[passwordVar]"
  AdditionalPermissions="AllowFiltering, AllowSorting" />
```

## Notes
- Either `Password` or `SecurePassword` must be set, but not both. Setting both causes a validation error.
- Setting neither `Password` nor `SecurePassword` also causes a validation error -- a password is required.
- Using a literal string for `Password` produces a validation warning; prefer `SecurePassword` or a variable for security.
- `AdditionalPermissions` is a flags enum -- multiple values can be combined.
- The `Password` and `SecurePassword` properties are toggled via a context menu in the designer (Use String / Use SecureString).
