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
| `Text` | Text | `InArgument` | `string` | Yes | — | The text to append. When the file already has content, a line break (`Environment.NewLine`) is written before the text; nothing is written after it. |
| `Encoding` | Encoding | `InArgument` | `string` | No | `null` | The encoding to use when appending, as a name (e.g. `"utf-8"`) or a code page number. When empty, the encoding is read from the file's byte-order mark; a new file, or a file without one, uses UTF-8 (see `UseDefaultEncoding`). Configurable as a project setting. |
| `UseDefaultEncoding` | Use default encoding | `InArgument` | `bool` | No | `false` | Applies only when `Encoding` is empty: when `true`, a new file or a file without a byte-order mark uses `System.Text.Encoding.Default` (UTF-8 without a byte-order mark on .NET 6 and later) instead of UTF-8 with one. |

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
- The line break goes before the text, never after it: two appends to a new file produce `a`, a line break, `b`, with no trailing line break. An append to a file that already ends with a line break leaves an empty line.
- A file counts as empty — no leading line break — at 0 bytes, or when its size equals the byte-order mark of the resolved encoding (3 bytes for UTF-8, 2 for UTF-16). A 3-byte UTF-8 file such as `x` plus a line break is therefore treated as empty.
- Creating the file, or appending to an empty one, writes the encoding's byte-order mark, so UTF-8 files start with `EF BB BF`. To write UTF-8 without it, leave `Encoding` empty and set `UseDefaultEncoding` to `true`.
- The `Encoding` property can be set at project level via **Project Settings** (`Section.AppendLine, Property.Encoding`).
- When `Encoding` is set, it is used and `UseDefaultEncoding` has no effect.
