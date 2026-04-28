# Create New Workbook

`UiPath.Excel.Activities.CreateNewWorkbook`

Creates a new Excel workbook at the specified file path.

**Package:** `UiPath.Excel.Activities`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `WorkbookPath` | File (local path) | InArgument | `string` | Yes | | The full local path where the new workbook will be created |
| `SheetName` | SheetName | InArgument | `string` | Yes | | The name of the initial sheet in the workbook |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ConflictResolution` | Conflict Behavior | `InArgument<ConflictBehavior>` | `Replace` | What to do if a file already exists at the path |
| `Password` | Password | `InArgument<string>` | | The password for the new workbook |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `WorkbookFile` | Workbook File | `Workbook` | The newly created Workbook object |

### Enum Reference

**`ConflictBehavior`**: `Replace`, `Skip`, `Error`

## XAML Example

```xml
<excel:CreateNewWorkbook
  DisplayName="Create New Workbook"
  WorkbookPath="[&quot;C:\Reports\new_report.xlsx&quot;]"
  SheetName="[&quot;Sheet1&quot;]"
  WorkbookFile="[newWorkbook]" />
```

## Notes

- Uses the file-based workbook engine (not Excel Interop). Works cross-platform.
- `WorkbookPathResource` is hidden for this activity — only local file path is supported.
- The `Workbook` input property (from base class) is hidden — this activity creates a new workbook rather than using an existing one.
