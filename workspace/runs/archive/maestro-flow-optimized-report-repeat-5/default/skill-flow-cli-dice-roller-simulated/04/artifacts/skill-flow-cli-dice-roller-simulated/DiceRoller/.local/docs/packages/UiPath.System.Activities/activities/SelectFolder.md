# Select Folder

`UiPath.Core.Activities.SelectFolder`

Opens a folder picker dialog and returns the selected folder path.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `SelectedFolder` | SelectedFolder | `OutArgument` | `string` | The selected folder path. |

## XAML Example

```xml
<ui:SelectFolder
    DisplayName="Select Folder"
    SelectedFolder="[folderPath]" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- This activity is Windows-only.
- The activity throws if the user cancels the selection dialog.
