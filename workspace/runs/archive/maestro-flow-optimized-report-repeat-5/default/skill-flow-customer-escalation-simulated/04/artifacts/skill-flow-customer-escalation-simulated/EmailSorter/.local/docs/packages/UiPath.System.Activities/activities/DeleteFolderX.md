# Delete Folder

`UiPath.Core.Activities.DeleteFolderX`

Deletes the specified folder.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Path` | Path | `InArgument` | `string` | Yes | - | Full path of the folder to delete. |
| `Recursive` | Recursive | `InArgument` | `bool` | No | `true` | When `true`, deletes subfolders and files recursively. |

## XAML Example

```xml
<ui:DeleteFolderX
    DisplayName="Delete Folder"
    Path="C:\temp\old-folder"
    Recursive="True" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- This activity is Windows-only.
- When `Recursive` is `false`, the folder must be empty.
