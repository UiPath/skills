# Download Storage File

`UiPath.Core.Activities.Storage.DownloadStorageFile`

Downloads a copy of a file in an Orchestrator storage bucket locally.

**Package:** `UiPath.System.Activities`
**Category:** Storage

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Path` | Path | InArgument | `string` | Yes | — | The path of the file within the storage bucket to download (e.g., `reports/output.pdf`). |
| `Destination` | Destination | InArgument | `string` | No | — | The local file system path where the downloaded file will be saved. If omitted, the file is saved in the current working directory using the source file's name. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | OutArgument | `ILocalResource` | A reference to the downloaded local file, providing access to the file name and full local path. |

## XAML Example

```xml
<ui:DownloadStorageFile
    xmlns:ui="clr-namespace:UiPath.Core.Activities.Storage;assembly=UiPath.System.Activities"
    DisplayName="Download Storage File"
    Path="[&quot;reports/output.pdf&quot;]"
    Destination="[&quot;C:\Temp\output.pdf&quot;]"
    Result="{x:Reference downloadedFile}" />
```

## Notes

- Requires an active Orchestrator connection with access to storage buckets.
- The storage bucket name and folder path are configured in the Orchestrator connection context (via `StorageBucketName` and `FolderPath` inherited from the base storage activity class).
- `Path` refers to the file's path within the Orchestrator storage bucket, not a local path.
- If `Destination` is not specified, the file is saved to the process working directory using only the filename portion of `Path`.
- If the destination file already exists locally, it is overwritten.
- The `Result` output provides an `ILocalResource` object. Use `Result.LocalPath` (via the `ILocalResource` interface) to get the full path of the downloaded file.
