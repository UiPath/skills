# List Storage Files

`UiPath.Core.Activities.Storage.ListStorageFiles`

Lists the content of a certain directory in an Orchestrator storage bucket.

**Package:** `UiPath.System.Activities`
**Category:** Storage

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `StorageBucketName` | Storage bucket name | InArgument | `string` | Yes (inherited) | — | The name of the Orchestrator storage bucket. Inherited from the storage activity base class — declared on the activity element, not as a child binding. |
| `FolderPath` | Folder path | InArgument | `string` | No (inherited) | — | The Orchestrator folder containing the storage bucket. Inherited from the storage activity base class. Leave empty to use the robot's current folder. |
| `Directory` | Directory | InArgument | `string` | Yes | `"\\"` | The path of the directory within the storage bucket to list (e.g., `reports/2024`). Defaults to the bucket root. |
| `Filter` | Filter | InArgument | `string` | No | — | An optional filter expression to narrow down results by file name or pattern. |
| `Recursive` | Recursive | InArgument | `bool` | No | `true` | When `True`, lists files in all subdirectories recursively. When `False`, lists only the immediate directory contents. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | OutArgument | `IEnumerable<StorageFileInfo>` (`UiPath.Core.Activities.Storage`) | Collection of file metadata entries for the listed directory. |

#### `StorageFileInfo` fields

`UiPath.Core.Activities.Storage.StorageFileInfo` — returned items expose three string fields:

| Field | Description |
|-------|-------------|
| `FileFullPath` | The file's full path within the storage bucket (folder + file name). |
| `StorageContainerName` | The name of the bucket the file resides in. |
| `StorageContainerFolderPath` | The Orchestrator folder path of the bucket. |

## XAML Example

```xml
<ui:ListStorageFiles
    xmlns:ui="clr-namespace:UiPath.Core.Activities.Storage;assembly=UiPath.System.Activities"
    DisplayName="List Storage Files"
    StorageBucketName="Finance"
    Directory="reports/2024"
    Recursive="False"
    Result="[fileList]" />
```

## Notes

- Requires an active Orchestrator connection with access to storage buckets.
- `StorageBucketName` is **required** (inherited from the storage activity base class). `FolderPath` is optional — when empty, the robot's current Orchestrator folder is used.
- `Directory` defaults to `"\\"` which represents the root of the bucket.
- The activity output `Result` is `IEnumerable<StorageFileInfo>`. Iterate it with **For Each** to access each entry's `FileFullPath`.
- `Recursive` defaults to `True`; set it to `False` to list only the top-level entries in the specified directory.
