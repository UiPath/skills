# Read Text File

`UiPath.Core.Activities.ReadTextFile`

Copies all the characters from a specified text file.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FileName` | Read Text File | `InArgument` | `string` | Yes* | — | Full path of the text file to read. Overload group: `FileName`. |
| `File` | File | `InArgument` | `IResource` | Yes* | — | Resource reference to the file to read. Overload group: `File`. |
| `Encoding` | Encoding | `InArgument` | `string` | No | `null` | The encoding to use when reading the file (e.g. `"utf-8"`, `"windows-1252"`). When `null`, the encoding is auto-detected. Configurable as a project setting. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Content` | Output | `OutArgument` | `string` | The full text content read from the file. |

## Valid Configurations

Two mutually exclusive overload groups determine how the file is specified:

| Mode | Property | Description |
|------|----------|-------------|
| Local path | `FileName` | String expression resolving to a local file path. |
| Resource | `File` | `IResource` expression (e.g. from Create File or Get Local File or Folder). |

## XAML Example

```xml
<ui:ReadTextFile
    DisplayName="Read Text File"
    FileName="&quot;C:\data\input.txt&quot;"
    Encoding="&quot;utf-8&quot;"
    Content="[fileContent]" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- The `Encoding` property can be set at project level via **Project Settings** (`Section.ReadTextFile, Property.Encoding`), avoiding repeated configuration across workflows.
- When `Encoding` is left empty, the activity attempts to detect the encoding automatically using byte-order marks (BOM).
- For large files, consider streaming alternatives to avoid high memory usage.
