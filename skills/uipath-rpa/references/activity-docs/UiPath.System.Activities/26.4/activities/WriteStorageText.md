# Write Storage Text

`UiPath.Core.Activities.Storage.WriteStorageText`

Saves an input String into a file in the Orchestrator storage, in a certain bucket and at a certain path.

**Package:** `UiPath.System.Activities`
**Category:** Storage

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Path` | Path | InArgument | `string` | Yes | — | The destination file path within the storage bucket (e.g., `data/output.txt`). |
| `Text` | Text | InArgument | `string` | Yes | — | The string content to write into the storage file. |
| `Encoding` | Encoding | InArgument | `string` | No | `null` | The character encoding to use when writing the text (e.g., `"utf-8"`, `"utf-16"`). Defaults to UTF-8 when not specified. Can be set as a project-level default. |

## XAML Example

```xml
<ui:WriteStorageText
    xmlns:ui="clr-namespace:UiPath.Core.Activities.Storage;assembly=UiPath.System.Activities"
    DisplayName="Write Storage Text"
    Path="[&quot;data/output.txt&quot;]"
    Text="[reportContent]"
    Encoding="[&quot;utf-8&quot;]" />
```

## Notes

- Requires an active Orchestrator connection with access to storage buckets.
- The storage bucket name and folder path are configured in the Orchestrator connection context (via `StorageBucketName` and `FolderPath` inherited from the base storage activity class).
- `Path` is the full file path within the bucket, including the file name and extension.
- If a file already exists at the specified `Path`, it is overwritten with the new content.
- `Encoding` can be configured as a project-level setting (section `WriteTextFile`, property `Encoding`) so it applies consistently across the project without setting it on each activity instance.
- To read the text content back from a storage file, use **Read Storage Text**.
