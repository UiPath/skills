# Get Folder Info

`UiPath.Core.Activities.GetFolderInfoX`

Creates a `DirectoryInfo` object for a specified folder path.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FolderPath` | Path | `InArgument` | `string` | Yes | - | Full path of the folder. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ThrowIfNotExists` | Throw If Not Exists | `bool` | `false` | When `true`, throws if the folder does not exist. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Output` | OutputTo | `OutArgument` | `DirectoryInfo` | The `System.IO.DirectoryInfo` object created for the path. |

## XAML Example

```xml
<ui:GetFolderInfoX
    DisplayName="Get Folder Info"
    FolderPath="C:\reports"
    ThrowIfNotExists="True"
    Output="[folderInfo]" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- This activity is Windows-only.
- When `ThrowIfNotExists` is `false`, the activity still returns a `DirectoryInfo` object for the supplied path.
