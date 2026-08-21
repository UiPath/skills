# Folder Exists

`UiPath.Core.Activities.FolderExistsX`

Checks whether a folder exists at the specified path.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Path` | Path | `InArgument` | `string` | Yes | - | Full path of the folder to check. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Exists` | Exists | `OutArgument` | `bool` | `true` when the path exists as a directory; otherwise `false`. |

## XAML Example

```xml
<ui:FolderExistsX
    DisplayName="Folder Exists"
    Path="C:\reports"
    Exists="[folderExists]" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- This activity is Windows-only.
- Files return `false`; use **File Exists** to check files.
