# Read Storage Text

`UiPath.Core.Activities.Storage.ReadStorageText`

Returns the text content of a certain file in an Orchestrator storage bucket.

**Package:** `UiPath.System.Activities`
**Category:** Storage

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Path` | Path | InArgument | `string` | Yes | — | The path of the file within the storage bucket to read (e.g., `data/output.txt`). |
| `Encoding` | Encoding | InArgument | `string` | No | `null` | The character encoding to use when reading the file (e.g., `"utf-8"`, `"utf-16"`). Defaults to UTF-8 when not specified. Can be set as a project-level default. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | OutArgument | `string` | The text content of the file read from the storage bucket. |

## XAML Example

```xml
<ui:ReadStorageText
    xmlns:ui="clr-namespace:UiPath.Core.Activities.Storage;assembly=UiPath.System.Activities"
    DisplayName="Read Storage Text"
    Path="[&quot;data/output.txt&quot;]"
    Encoding="[&quot;utf-8&quot;]"
    Result="{x:Reference fileContent}" />
```

## Notes

- Requires an active Orchestrator connection with access to storage buckets.
- The storage bucket name and folder path are configured in the Orchestrator connection context (via `StorageBucketName` and `FolderPath` inherited from the base storage activity class).
- `Path` is the full file path within the bucket, including the file name and extension.
- `Encoding` can be configured as a project-level setting (section `ReadTextFile`, property `Encoding`) so it applies consistently across the project without setting it on each activity instance.
- If the file does not exist in the bucket, the activity throws a runtime error.
- To write text content to a storage file, use **Write Storage Text**.
