# Delete Storage File

`UiPath.Core.Activities.Storage.DeleteStorageFile`

Deletes a certain file from the designated Orchestrator storage bucket.

**Package:** `UiPath.System.Activities`
**Category:** Storage

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Path` | Path | InArgument | `string` | Yes | — | The path of the file to delete within the storage bucket (e.g., `reports/output.pdf`). |

## XAML Example

```xml
<ui:DeleteStorageFile
    xmlns:ui="clr-namespace:UiPath.Core.Activities.Storage;assembly=UiPath.System.Activities"
    DisplayName="Delete Storage File"
    Path="[&quot;reports/output.pdf&quot;]" />
```

## Notes

- Requires an active Orchestrator connection with access to storage buckets.
- The storage bucket name and folder path are configured in the Orchestrator connection context (via `StorageBucketName` and `FolderPath` inherited from the base storage activity class).
- `Path` is the path of the file within the bucket, not a local file system path.
- If the file does not exist in the bucket, the activity throws a runtime error.
- This operation is permanent and cannot be undone.
