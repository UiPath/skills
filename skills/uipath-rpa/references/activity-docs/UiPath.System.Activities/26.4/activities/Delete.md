# Delete File or Folder

`UiPath.Core.Activities.Delete`

Deletes the file or folder in the specified location.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Path` | Delete | `InArgument` | `string` | Yes* | — | Full path of the file or folder to delete. Overload group: `Path`. |
| `ResourceFile` | File | `InArgument` | `ILocalResource` | Yes* | — | Local resource reference to the file or folder to delete. Overload group: `ResourceFile`. |
| `ContinueOnError` | Continue On Error | `InArgument` | `bool` | No | — | When `true`, execution continues even if an error occurs. |

## Valid Configurations

Two mutually exclusive overload groups are supported:

| Mode | Property | Description |
|------|----------|-------------|
| Path string | `Path` | String expression resolving to a local file or folder path. |
| Resource | `ResourceFile` | `ILocalResource` reference (e.g. output of Create File or Create Folder). |

## XAML Example

```xml
<ui:Delete
    DisplayName="Delete File or Folder"
    Path="&quot;C:\temp\old_report.pdf&quot;" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- When deleting a folder, all contents (files and subfolders) are removed recursively.
- This activity produces no output argument.
- If the specified path does not exist and `ContinueOnError` is `false`, the activity raises an error.
