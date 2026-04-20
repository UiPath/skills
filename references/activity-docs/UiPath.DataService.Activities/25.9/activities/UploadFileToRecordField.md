# UploadFileToRecordField

Uploads a file to a file-type field on an entity record. Category: **DataService.File**.

## Properties

| Property | Type | Required | Default | Category | Description |
|----------|------|----------|---------|----------|-------------|
| `x:TypeArguments` | — | Yes | — | — | Concrete entity type: `local:EntityName` |
| `EntityId` | `InArgument<Guid>` | Yes | — | — | Entity GUID from `EntitiesStore.json` |
| `RecordId` | `InArgument<Guid>` | Yes | — | Input | GUID of the target record (`[RequiredArgument]`) |
| `Field` | `InArgument<string>` | Yes | — | Input | Name of the file field (`[RequiredArgument]`, `[Browsable(false)]`) |
| `FilePath` | `InArgument<string>` | Cond. | — | Input | Local file path to upload (one of `FilePath` or `FileResource` required) |
| `FileResource` | `InArgument<IResource>` | Cond. | — | Input | Resource object to upload (alternative to `FilePath`) |
| `ExpansionDepth` | `InArgument<int>` | No | `2` | Options | Depth of relationship expansion in response (range: 1–3) |
| `OutputEntity` | `OutArgument<TEntity>` | No | — | Output | Receives the updated entity after upload |
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Common | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Common | Timeout in milliseconds |

> **Solution scope properties** (`ScopeValue`, `SolutionEntityKey`, `SolutionEntityName`) only apply when the project has a SolutionId. For standalone projects, omit them. See [overview — Solution Scope Properties](overview.md#solution-scope-properties-conditional) and [Solution Context](overview.md#solution-context-folder-vs-tenant-scope).

## XAML Example

```xml
<uda:UploadFileToRecordField
    x:TypeArguments="local:ENTITY_NAME"
    ContinueOnError="False"
    DisplayName="Upload File to ENTITY_NAME"
    EntityId="ENTITY_GUID"
    RecordId="[recordIdVariable]"
    Field="[&quot;FileFieldName&quot;]"
    FilePath="[&quot;C:\\path\\to\\file.pdf&quot;]"
    ExpansionDepth="2"
    OutputEntity="[updatedEntity]"
    TimeoutInMs="30000" />
```

## Round-Trip Pattern (Download → Upload)

When copying a file from one record to another, use `FileResource` — not `FilePath` — to chain the download output directly:

```xml
<!-- Download captures DownloadedFileResource (ILocalResource) -->
<uda:DownloadFileFromRecordField
    x:TypeArguments="local:SOURCE_ENTITY"
    DisplayName="Download File"
    EntityId="SOURCE_ENTITY_GUID"
    RecordId="[sourceRecordId]"
    Field="[&quot;FileFieldName&quot;]"
    DownloadedFileResource="[downloadedFile]"
    TimeoutInMs="30000" />

<!-- Upload consumes it via FileResource (IResource) — preserves original filename -->
<uda:UploadFileToRecordField
    x:TypeArguments="local:TARGET_ENTITY"
    DisplayName="Upload File"
    EntityId="TARGET_ENTITY_GUID"
    RecordId="[targetRecordId]"
    Field="[&quot;FileFieldName&quot;]"
    FileResource="[downloadedFile]"
    ExpansionDepth="2"
    TimeoutInMs="30000" />
```

> **Prefer `FileResource` over `FilePath`** when the source is another activity's output. `ILocalResource` (from `DownloadFileFromRecordField`) is assignment-compatible with `IResource`. Using `FilePath` with a fabricated temp path loses the original filename metadata.

## Key Rules

- Either `FilePath` or `FileResource` must be provided — if both are null, validation fails
- **Prefer `FileResource` for round-trip file copies** — pass the `ILocalResource` from download directly; this preserves the original filename
- If `FileResource` is provided, it is resolved to a local path at runtime via `ToLocalResource().ResolveAsync()`
- The `Field` property must match a field with `FieldDisplayType: "File"` in `EntitiesStore.json`
