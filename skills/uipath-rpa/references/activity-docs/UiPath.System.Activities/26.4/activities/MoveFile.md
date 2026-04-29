# Move File

`UiPath.Core.Activities.MoveFile`

Moves a specified file to another location.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Path` | Move File | `InArgument` | `string` | Yes* | — | Full path of the source file. Overload group: `Path`. |
| `PathResource` | Input resource | `InArgument` | `IResource` | Yes* | — | Resource reference to the source file. Overload group: `PathResource`. |
| `Destination` | Destination | `InArgument` | `string` | No | — | Destination path or folder for the moved file. |
| `DestinationResource` | Destination resource | `InArgument` | `IResource` | No | — | Resource reference to the destination. |
| `ContinueOnError` | Continue On Error | `InArgument` | `bool` | No | — | When `true`, execution continues even if an error occurs. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Overwrite` | Overwrite | `bool` | `false` | When `true`, overwrites the destination file if it already exists. |

## Valid Configurations

| Mode | Source property | Destination property |
|------|----------------|---------------------|
| Local path | `Path` | `Destination` |
| Resource | `PathResource` | `DestinationResource` |

Source overload groups are `Path` and `PathResource`; these are mutually exclusive. Destination properties can be used independently of the source mode.

## XAML Example

```xml
<ui:MoveFile
    DisplayName="Move File"
    Path="&quot;C:\inbox\report.pdf&quot;"
    Destination="&quot;C:\processed\report.pdf&quot;"
    Overwrite="False" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- If `Destination` is an existing **folder**, the source file is moved into that folder keeping its original name.
- This activity produces no output argument.
- Moving a file across volumes performs a copy-then-delete operation internally.
