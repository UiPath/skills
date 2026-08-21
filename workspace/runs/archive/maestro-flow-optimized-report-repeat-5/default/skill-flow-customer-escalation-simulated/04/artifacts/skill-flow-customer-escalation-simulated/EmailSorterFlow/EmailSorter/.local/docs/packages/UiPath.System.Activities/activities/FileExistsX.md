# File Exists

`UiPath.Core.Activities.FileExistsX`

Checks whether a file exists at the specified path.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Path` | Path | `InArgument` | `string` | Yes | - | Full path of the file to check. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Exists` | Exists | `OutArgument` | `bool` | `true` when the path exists as a file; otherwise `false`. |

## XAML Example

```xml
<ui:FileExistsX
    DisplayName="File Exists"
    Path="C:\reports\summary.xlsx"
    Exists="[fileExists]" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- This activity is Windows-only.
- Directories return `false`; use **Folder Exists** to check folders.
