# Append Line

`UiPath.Core.Activities.AppendLine`

Adds the specified text to a file after the existing content. If it does not already exist, the file is created.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FileName` | Append Line | `InArgument` | `string` | Yes* | — | Full path of the file to append to. Overload group: `FileName`. |
| `File` | File | `InArgument` | `ILocalResource` | Yes* | — | Local resource reference to the file to append to. Overload group: `File`. |
| `Text` | Text | `InArgument` | `string` | Yes | — | The text to append. A newline is added after the existing content before writing. |
| `Encoding` | Encoding | `InArgument` | `string` | No | `null` | The encoding to use when appending (e.g. `"utf-8"`). When `null`, the system default is used. Configurable as a project setting. |
| `UseDefaultEncoding` | Use default encoding | `InArgument` | `bool` | No | `false` | When `true`, ignores the `Encoding` value and uses the system default encoding. |

## Valid Configurations

Two mutually exclusive modes determine how the file is specified:

| Mode | Property | Description |
|------|----------|-------------|
| Local path | `FileName` | String expression resolving to a local file path. |
| Resource | `File` | `ILocalResource` expression (e.g. from Create File). |

## XAML Example

```xml
<ui:AppendLine
    DisplayName="Append Line"
    FileName="&quot;C:\logs\process.log&quot;"
    Text="[logEntry]"
    Encoding="&quot;utf-8&quot;" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- Unlike **Write Text File**, this activity preserves existing file content and adds the new text after it.
- If the target file does not exist, it is created.
- The `Encoding` property can be set at project level via **Project Settings** (`Section.AppendLine, Property.Encoding`).
- When `UseDefaultEncoding` is `true`, the `Encoding` argument is ignored regardless of its value.
