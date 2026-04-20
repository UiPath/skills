# DownloadFileFromRecordField

Downloads a file from a file-type field on an entity record. Category: **DataService.File**.

## Properties

| Property | Type | Required | Default | Category | Description |
|----------|------|----------|---------|----------|-------------|
| `x:TypeArguments` | — | Yes | — | — | Concrete entity type: `local:EntityName` |
| `EntityId` | `InArgument<Guid>` | Yes | — | — | Entity GUID from `EntitiesStore.json` |
| `RecordId` | `InArgument<Guid>` | Yes | — | Input | GUID of the source record (`[RequiredArgument]`) |
| `Field` | `InArgument<string>` | Yes | — | Input | Name of the file field (`[RequiredArgument]`, `[Browsable(false)]`) |
| `FilePath` | `InArgument<string>` | No | — | To | Local path to save the downloaded file |
| `DownloadedFileResource` | `OutArgument<ILocalResource>` | No | — | Output | Resource object pointing to the downloaded file |
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Common | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Common | Timeout in milliseconds |

> **Solution scope properties** (`ScopeValue`, `SolutionEntityKey`, `SolutionEntityName`) only apply when the project has a SolutionId. For standalone projects, omit them. See [overview — Solution Scope Properties](overview.md#solution-scope-properties-conditional) and [Solution Context](overview.md#solution-context-folder-vs-tenant-scope).

No `ExpansionDepth` — download returns a file, not an entity.

## XAML Example

```xml
<uda:DownloadFileFromRecordField
    x:TypeArguments="local:ENTITY_NAME"
    ContinueOnError="False"
    DisplayName="Download File from ENTITY_NAME"
    EntityId="ENTITY_GUID"
    RecordId="[recordIdVariable]"
    Field="[&quot;FileFieldName&quot;]"
    FilePath="[&quot;C:\\downloads\\output.pdf&quot;]"
    DownloadedFileResource="[fileResource]"
    TimeoutInMs="30000" />
```

## Round-Trip Pattern (Download → Upload)

When copying a file between records, chain `DownloadedFileResource` directly into `UploadFileToRecordField.FileResource`. This preserves the original filename and avoids fabricating temp paths.

```xml
<!-- Step 1: Download — capture DownloadedFileResource, omit FilePath -->
<uda:DownloadFileFromRecordField
    x:TypeArguments="local:SOURCE_ENTITY"
    DisplayName="Download File from Source"
    EntityId="SOURCE_ENTITY_GUID"
    RecordId="[sourceRecordId]"
    Field="[&quot;FileFieldName&quot;]"
    DownloadedFileResource="[downloadedFile]"
    TimeoutInMs="30000" />

<!-- Step 2: Upload — pass downloadedFile as FileResource, not FilePath -->
<uda:UploadFileToRecordField
    x:TypeArguments="local:TARGET_ENTITY"
    DisplayName="Upload File to Target"
    EntityId="TARGET_ENTITY_GUID"
    RecordId="[targetRecordId]"
    Field="[&quot;FileFieldName&quot;]"
    FileResource="[downloadedFile]"
    ExpansionDepth="2"
    TimeoutInMs="30000" />
```

> **Prefer `FileResource` over `FilePath`** when the file originates from another activity. `ILocalResource` (from download) is assignment-compatible with `IResource` (upload input). Using `FilePath` with a fabricated temp path loses the original filename metadata.

Variable declarations needed:
- `downloadedFile` — type `UiPath.DataService.Activities.Resources.ILocalResource` (from download `OutArgument`)
- The upload accepts `IResource` — `ILocalResource` satisfies this interface

## Key Rules

- `DownloadedFileResource` returns an `ILocalResource` with the local file path — use `.LocalPath` to get the path
- If `FilePath` is specified, the file is saved to that location; otherwise a temporary location is used
- **For round-trip file copies, omit `FilePath` and use `DownloadedFileResource` → `FileResource` chaining** — see pattern above
