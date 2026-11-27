# List Storage Files

`UiPath.Core.Activities.Storage.ListStorageFiles`

Lists the content of a certain directory in an Orchestrator storage bucket.

**Package:** `UiPath.System.Activities`
**Category:** Storage

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Directory` | Directory | InArgument | `string` | Yes | `"\\"` | The path of the directory within the storage bucket to list (e.g., `reports/2024`). Defaults to the bucket root. |
| `Filter` | Filter | InArgument | `string` | No | — | An optional filter expression to narrow down results by file name or pattern. |
| `Recursive` | Recursive | InArgument | `bool` | No | `true` | When `True`, lists files in all subdirectories recursively. When `False`, lists only the immediate directory contents. |

## XAML Example

```xml
<ui:ListStorageFiles
    xmlns:ui="clr-namespace:UiPath.Core.Activities.Storage;assembly=UiPath.System.Activities"
    DisplayName="List Storage Files"
    Directory="[&quot;reports/2024&quot;]"
    Recursive="[False]" />
```

## Notes

- Requires an active Orchestrator connection with access to storage buckets.
- The storage bucket name and folder path are configured in the Orchestrator connection context (via `StorageBucketName` and `FolderPath` inherited from the base storage activity class).
- `Directory` defaults to `"\\"` which represents the root of the bucket.
- The activity returns a collection of file metadata objects. Iterate over the result to access individual file details such as name and path.
- `Recursive` defaults to `True`; set it to `False` to list only the top-level entries in the specified directory.
