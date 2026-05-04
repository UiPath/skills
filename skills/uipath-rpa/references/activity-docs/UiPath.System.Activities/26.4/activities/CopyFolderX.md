# Copy Folder

`UiPath.Core.Activities.CopyFolderX`

Copies a specified folder to another location.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `From` | From | `InArgument` | `string` | Yes* | — | Full path of the source folder. Visible when `FromResource` has no value. |
| `FromResource` | Source Folder Resource | `InArgument` | `IResource` | Yes* | — | Resource reference to the source folder. Visible when `From` has no value. |
| `To` | To | `InArgument` | `string` | Yes* | — | Destination path for the copied folder. Visible when `ToResource` has no value. |
| `ToResource` | Destination Folder Resource | `InArgument` | `IResource` | Yes* | — | Resource reference to the destination folder. Visible when `To` has no value. |
| `ContinueOnError` | Continue On Error | `InArgument` | `bool` | No | `null` | When `true`, execution continues even if an error occurs. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `IncludeSubfolders` | Include subfolders | `bool` | `true` | When `true`, copies all subfolders recursively. |
| `Overwrite` | Overwrite | `bool` | `true` | When `true`, overwrites files in the destination that already exist. |

## Valid Configurations

Both source and destination support two mutually exclusive input modes toggled via context menu in Studio:

| Mode | Property | Description |
|------|----------|-------------|
| Local path (source) | `From` | String expression resolving to a local folder path. Default mode. |
| Resource (source) | `FromResource` | `IResource` expression for the source folder. |
| Local path (destination) | `To` | String expression resolving to a local folder path. Default mode. |
| Resource (destination) | `ToResource` | `IResource` expression for the destination folder. |

## XAML Example

```xml
<ui:CopyFolderX
    DisplayName="Copy Folder"
    From="&quot;C:\source\reports&quot;"
    To="&quot;C:\archive\reports&quot;"
    IncludeSubfolders="True"
    Overwrite="True" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- The copy is recursive by default (`IncludeSubfolders = true`).
- This activity produces no output argument.
