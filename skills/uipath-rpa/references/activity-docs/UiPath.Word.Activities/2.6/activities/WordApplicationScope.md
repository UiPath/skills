# Word Application Scope

`UiPath.Word.Activities.WordApplicationScope`

Opens a Word document and provides a scope for other Word activities. When this activity ends, the document and the Word application are closed. If the specified file does not exist and `CreateNewFile` is enabled, a new document file is created.

**Package:** `UiPath.Word.Activities`
**Category:** Word
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FilePath` | File path | InArgument | `string` | Yes | | The path to the Word document to open |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `AutoSave` | Auto save | `bool` | `true` | Automatically saves the document when the scope ends |
| `CreateNewFile` | Create if not exists | `bool` | `true` | Creates a new document if the file does not exist. Only supported for local file system paths |
| `ReadOnly` | ReadOnly | `bool` | `false` | Opens the document in read-only mode |
| `SensitivityOperation` | Sensitivity operation | `WordLabelOperation` | `None` | Sensitivity label operation to apply. Use `Add` with `SensitivityLabel` to set a label, or `Clear` to remove it |
| `SensitivityLabel` | Sensitivity label | InArgument | `object` | Conditional | | A sensitivity label ID (string) or `IWordLabelObject` instance. Required when `SensitivityOperation` is `Add` (raises a validation error if missing) |

### Enum Reference

**`WordLabelOperation`**: `None` (no operation), `Add` (add or update label), `Clear` (remove label)

## XAML Example

```xml
<ui:WordApplicationScope
    DisplayName="Word Application Scope"
    FilePath="[documentPath]"
    AutoSave="True"
    CreateNewFile="True">
    <ui:WordApplicationScope.Body>
        <ActivityAction x:TypeArguments="x:Object">
            <Sequence>
                <!-- Place Word activities here -->
            </Sequence>
        </ActivityAction>
    </ui:WordApplicationScope.Body>
</ui:WordApplicationScope>
```

## Notes

- Windows only — requires Microsoft Word installed
- This is a scope (container) activity. All Windows Word activities must be placed inside it
- Opens a Word COM Interop session; the Word process is closed when the scope completes
- Sensitivity label operations require Microsoft Information Protection (MIP) to be configured
