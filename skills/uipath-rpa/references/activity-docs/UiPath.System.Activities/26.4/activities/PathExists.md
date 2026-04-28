# Get Local File or Folder

`UiPath.Core.Activities.PathExists`

Checks if the specified path exists. The path can represent a file path or a directory path.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Path` | Get Local File or Folder | `InArgument` | `string` | Yes | — | The file or folder path to check for existence. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `PathType` | PathType | `PathType` | — | Constrains the check to a specific type: `Any`, `File`, or `Directory`. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Exists` | File or folder exists | `OutArgument` | `bool` | `true` if the path exists (and matches the specified `PathType`); otherwise `false`. |
| `Resource` | File or folder object | `OutArgument` | `ILocalResource` | Reference to the existing file or folder resource. `null` if it does not exist. |

## XAML Example

```xml
<ui:PathExists
    DisplayName="Get Local File or Folder"
    Path="&quot;C:\reports\summary.xlsx&quot;"
    Exists="[fileExists]"
    Resource="[fileResource]" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- Use the `Exists` output to branch execution with an **If** activity before attempting to read or manipulate the file.
- The `Resource` output provides an `ILocalResource` suitable for use with other file activities without requiring a separate path string.
- When `PathType` is set to `File`, a path that exists as a directory returns `Exists = false`, and vice versa.
