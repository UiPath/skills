# Move Folder

`UiPath.Core.Activities.MoveFolderX`

Moves a folder into another existing folder.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `From` | From | `InArgument` | `string` | Yes | - | Full path of the folder to move. |
| `To` | To | `InArgument` | `string` | Yes | - | Destination parent folder. The moved folder keeps its original name. |
| `Overwrite` | Overwrite | Property | `bool` | No | `true` | When `true`, overwrites files in the destination folder if needed. |

## XAML Example

```xml
<ui:MoveFolderX
    DisplayName="Move Folder"
    From="C:\work\reports"
    To="C:\archive"
    Overwrite="True" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- This activity is Windows-only.
- `To` must be an existing folder and cannot be the source folder's current parent.
- The destination cannot be a subfolder of the source folder.
