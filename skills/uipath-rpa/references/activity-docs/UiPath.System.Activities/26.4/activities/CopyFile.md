# Copy File

`UiPath.Core.Activities.CopyFile`

Copies a specified file to another location.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Path` | From | `InArgument` | `string` | Yes* | — | Full path of the source file to copy. Mutually exclusive with `PathResource`. |
| `PathResource` | From | `InArgument` | `IResource` | Yes* | — | Resource reference to the source file. Mutually exclusive with `Path`. |
| `Destination` | To | `InArgument` | `string` | Yes* | — | Destination path or folder for the copied file. Mutually exclusive with `DestinationResource`. |
| `DestinationResource` | To | `InArgument` | `IResource` | Yes* | — | Resource reference to the destination. Mutually exclusive with `Destination`. |
| `ContinueOnError` | Continue On Error | `InArgument` | `bool` | No | — | When `true`, execution continues even if an error occurs. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Overwrite` | Overwrite | `bool` | `false` | When `true`, overwrites the destination file if it already exists. |

## Valid Configurations

Each of the source and destination supports two mutually exclusive input modes, toggled via a context menu action in Studio:

| Mode | Property | Description |
|------|----------|-------------|
| Local path (source) | `Path` | String expression resolving to a local file path. Default mode. |
| Resource (source) | `PathResource` | `IResource` expression (e.g. a Storage Bucket file resource). |
| Local path (destination) | `Destination` | String expression resolving to a local path or folder. Default mode. |
| Resource (destination) | `DestinationResource` | `IResource` expression for the destination. |

Only one property per pair is visible at a time. A validation error is raised if neither the path nor the resource is provided for either side.

## XAML Example

```xml
<ui:CopyFile
    DisplayName="Copy File"
    Path="&quot;C:\source\report.pdf&quot;"
    Destination="&quot;C:\archive\report.pdf&quot;"
    Overwrite="True" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- If `Destination` resolves to an existing **folder**, the source file is copied into that folder keeping its original name.
- If `Destination` is a full file path, the parent directory must already exist.
- This activity produces no output argument. The resulting file path equals the resolved destination value.
