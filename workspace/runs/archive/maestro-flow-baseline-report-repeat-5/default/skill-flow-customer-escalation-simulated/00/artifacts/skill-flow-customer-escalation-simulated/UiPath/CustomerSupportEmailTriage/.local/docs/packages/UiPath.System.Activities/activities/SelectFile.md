# Select File

`UiPath.Core.Activities.SelectFile`

Opens a file picker dialog and returns the selected file path or paths.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Filter` | Filter | Property | `string` | No | `All files (*.*)\|*.*` | File dialog filter string. |
| `InitialDirectory` | Initial Directory | `InArgument` | `string` | No | - | Folder opened when the dialog appears. |
| `Multiselect` | Multiselect | `InArgument` | `bool` | No | `false` | Allows selecting multiple files. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `SelectedFile` | Selected file | `OutArgument` | `string` | The selected file path. When `Multiselect` is `true`, this is the first selected file. |
| `SelectedFiles` | Selected files | `OutArgument` | `IEnumerable<string>` | All selected file paths when `Multiselect` is `true`. |

## XAML Example

```xml
<ui:SelectFile
    DisplayName="Select File"
    Filter="Text files (*.txt)|*.txt|All files (*.*)|*.*"
    InitialDirectory="C:\input"
    SelectedFile="[filePath]" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- This activity is Windows-only.
- The activity throws if the user cancels the selection dialog.
- Multiple selected paths are separated internally and exposed through `SelectedFiles`.
