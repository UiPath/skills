# Unprotect Sheet

`UiPath.Excel.Activities.Business.UnprotectSheetX`

Unprotects a sheet in an Excel workbook.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Sheet` | Sheet | InArgument | `ISheetRef` | Yes | | Choose sheet to unprotect. |
| `Password` | Password | InArgument | `string` | Conditional | | Password to unprotect the sheet. |
| `SecurePassword` | Password (SecureString) | InArgument | `SecureString` | Conditional | | Password to unprotect the sheet as a SecureString type. |

## XAML Example
```xml
<excel:UnprotectSheetX
  DisplayName="Unprotect Sheet"
  Sheet="[sheetReference]"
  Password="[passwordVar]" />
```

## Notes
- Either `Password` or `SecurePassword` must be set, but not both. Setting both causes a validation error.
- Setting neither `Password` nor `SecurePassword` also causes a validation error -- a password is required.
- Using a literal string for `Password` produces a validation warning; prefer `SecurePassword` or a variable for security.
- The `Password` and `SecurePassword` properties are toggled via a context menu in the designer (Use String / Use SecureString).
