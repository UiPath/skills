# Upload Storage File

`UiPath.Core.Activities.Storage.UploadStorageFile`

Uploads a local file to the Orchestrator storage, in a certain bucket and at a certain path.

**Package:** `UiPath.System.Activities`
**Category:** Storage

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FileResource` | File Resource | InArgument | `IResource` | Yes (File overload) | — | A file resource object representing the local file to upload. Use this or `Path`, not both. |
| `Path` | Path | InArgument | `string` | Yes (Path overload) | — | The local file system path of the file to upload. Use this or `FileResource`, not both. |
| `Destination` | Destination | InArgument | `string` | Yes | — | The target directory path within the storage bucket where the file will be stored (e.g., `reports/2024`). |
| `FileName` | File Name | InArgument | `string` | No | — | The name to use for the file in the storage bucket. If omitted, the name is derived automatically from `FileResource` or `Path`. |

## Valid Configurations

`FileResource` and `Path` are mutually exclusive overload groups:

| Configuration | Required properties |
|---|---|
| **File** | `FileResource`, `Destination` |
| **Path** | `Path`, `Destination` |

## XAML Example

```xml
<!-- Upload using a local file path -->
<ui:UploadStorageFile
    xmlns:ui="clr-namespace:UiPath.Core.Activities.Storage;assembly=UiPath.System.Activities"
    DisplayName="Upload Storage File"
    Path="[&quot;C:\Temp\report.pdf&quot;]"
    Destination="[&quot;reports/2024&quot;]"
    FileName="[&quot;report.pdf&quot;]" />
```

```xml
<!-- Upload using a file resource -->
<ui:UploadStorageFile
    xmlns:ui="clr-namespace:UiPath.Core.Activities.Storage;assembly=UiPath.System.Activities"
    DisplayName="Upload Storage File"
    FileResource="[myFileResource]"
    Destination="[&quot;reports/2024&quot;]" />
```

## Notes

- Requires an active Orchestrator connection with access to storage buckets.
- The storage bucket name and folder path are configured in the Orchestrator connection context (via `StorageBucketName` and `FolderPath` inherited from the base storage activity class).
- `Destination` is the directory path within the bucket (not including the file name). The file name is specified separately via `FileName`.
- When `FileName` is left empty, the designer auto-populates it by deriving the name from `FileResource` or `Path`. If the `Destination` value previously included a filename (legacy format), it is automatically split into folder and filename parts during migration.
- If a file with the same name already exists at the destination path in the bucket, it is overwritten.
