# Rename File

`UiPath.Core.Activities.RenameFileX`

Renames the selected file.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FilePath` | File Path | `InArgument` | `string` | Yes* | — | Full path of the file to rename. Mutually exclusive with `FileResource`. |
| `FileResource` | File Resource | `InArgument` | `IResource` | Yes* | — | Resource reference to the file to rename. Mutually exclusive with `FilePath`. |
| `NewName` | New name | `InArgument` | `string` | Yes | — | The new name for the file. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `KeepExtension` | Keep extension | `bool` | `true` | When `true`, the original file extension is preserved even if `NewName` does not include one. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `OutputFileResource` | Renamed File | `OutArgument` | `IResource` | Reference to the renamed file. |

## Valid Configurations

The file to rename supports two mutually exclusive input modes:

| Mode | Property | Overload group |
|------|----------|----------------|
| Local path | `FilePath` | `File` |
| Resource | `FileResource` | `FileResource` |

`FilePath` is visible by default when `FileResource` has no value. `FileResource` is shown when `FilePath` has no value.

## XAML Example

```xml
<ui:RenameFileX
    DisplayName="Rename File"
    FilePath="&quot;C:\reports\old_name.xlsx&quot;"
    NewName="&quot;new_name&quot;"
    KeepExtension="True"
    OutputFileResource="[renamedFile]" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- When `KeepExtension` is `true` and `NewName` omits the extension, the original extension is appended automatically.
- When `KeepExtension` is `false`, `NewName` must include the desired extension explicitly.
