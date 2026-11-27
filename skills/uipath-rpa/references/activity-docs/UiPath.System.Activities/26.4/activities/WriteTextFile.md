# Write Text File

`UiPath.Core.Activities.WriteTextFile`

Copies a text and pastes it in a text file replacing any existing data in the file.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FileName` | Write Text File | `InArgument` | `string` | Yes* | — | Full path of the text file to write. Overload group: `FileName`. |
| `File` | File | `InArgument` | `ILocalResource` | Yes* | — | Local resource reference to the file to write. Overload group: `File`. |
| `Text` | Text | `InArgument` | `string` | Yes | — | The text content to write to the file. |
| `Encoding` | Encoding | `InArgument` | `string` | No | `null` | The encoding to use when writing the file (e.g. `"utf-8"`). When `null`, the system default encoding is used. Configurable as a project setting. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Output` | Output | `OutArgument` | `ILocalResource` | Reference to the written file. |

## Valid Configurations

Two mutually exclusive modes determine how the file is specified:

| Mode | Property | Description |
|------|----------|-------------|
| Local path | `FileName` | String expression resolving to a local file path. Default mode. |
| Resource | `File` | `ILocalResource` expression (e.g. from Create File). |

The mode is toggled via a context menu action in Studio. Only one property is visible at a time.

## XAML Example

```xml
<ui:WriteTextFile
    DisplayName="Write Text File"
    FileName="&quot;C:\output\result.txt&quot;"
    Text="[reportText]"
    Encoding="&quot;utf-8&quot;"
    Output="[writtenFile]" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- This activity **overwrites** all existing content in the target file. To append content instead, use the **Append Line** activity.
- If the specified file does not exist, it is created automatically.
- The `Encoding` property can be set at project level via **Project Settings** (`Section.WriteTextFile, Property.Encoding`).
