# Delete File

`UiPath.Core.Activities.DeleteFileX`

Deletes the specified file.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Path` | Path | `InArgument` | `string` | Yes | - | Full path of the file to delete. |

## XAML Example

```xml
<ui:DeleteFileX
    DisplayName="Delete File"
    Path="C:\temp\old-report.txt" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- This activity is Windows-only.
- The activity calls `System.IO.File.Delete`. If the file does not exist, no exception is thrown by `File.Delete`.
