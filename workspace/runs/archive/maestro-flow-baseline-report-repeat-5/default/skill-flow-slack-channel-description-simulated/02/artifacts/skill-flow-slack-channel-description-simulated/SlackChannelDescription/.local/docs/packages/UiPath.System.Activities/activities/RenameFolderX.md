# Rename Folder

`UiPath.Core.Activities.RenameFolderX`

Renames a folder without moving it to a different parent folder.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FolderPath` | Folder | `InArgument` | `string` | Yes | - | Full path of the folder to rename. |
| `NewName` | New name | `InArgument` | `string` | Yes | - | New folder name, without a parent path. |

## XAML Example

```xml
<ui:RenameFolderX
    DisplayName="Rename Folder"
    FolderPath="C:\archive\old-name"
    NewName="new-name" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- This activity is Windows-only.
- `NewName` cannot be empty and cannot contain invalid path characters such as `<`, `>`, `:`, `"`, `/`, `\`, `|`, `?`, or `*`.
