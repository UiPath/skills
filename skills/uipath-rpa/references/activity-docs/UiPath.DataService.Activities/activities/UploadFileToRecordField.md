# Upload File To Record Field

`UiPath.DataService.Activities.UploadFileToRecordField<TEntity>`

**Package:** `UiPath.DataService.Activities`

Uploads a file to a file-type field on an entity record.

**Category:** Data Service.File

## Properties

`x:TypeArguments` — concrete entity type, e.g. `local:EntityName`. Required at activity declaration.

### Input

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `EntityId` | `InArgument<Guid>` | Yes | — | Entity GUID from `EntitiesStore.json` |
| `RecordId` | `InArgument<Guid>` | Yes | — | GUID of the target record (`[RequiredArgument]`) |
| `Field` | `InArgument<string>` | Yes | — | Name of the file field (`[RequiredArgument]`, `[Browsable(false)]`) |
| `FilePath` | `InArgument<string>` | Cond. | — | Local file path to upload (one of `FilePath` or `FileResource` required). **Max file size: 10 MB.** |
| `FileResource` | `InArgument<IResource>` | Cond. | — | Resource object to upload (alternative to `FilePath`). **Max file size: 10 MB.** |
| `ExpansionDepth` | `InArgument<int>` | No | `2` | Depth of relationship expansion on the returned entity (range: 1–3, max `3`) — see [overview § Relationship Fields & ExpansionDepth](../overview.md#relationship-fields--expansiondepth) |

### Output

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `OutputEntity` | `OutArgument<TEntity>` | No | — | Receives the updated entity after upload |

### Common

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Timeout in milliseconds |

> **Solution scope properties** (`ScopeValue`, `SolutionEntityKey`, `SolutionEntityName`) are inherited from `BaseEntityActivity` and exist on every activity, but only apply when the project has a SolutionId. For standalone projects, omit them — they're ignored outside solution context. See [overview — Solution Scope Properties](../overview.md#solution-scope-properties-conditional) and [Solution Context](../overview.md#solution-context-folder-vs-tenant-scope).

## XAML Example — Upload from FilePath

```xml
<uda:UploadFileToRecordField
    x:TypeArguments="local:ENTITY_NAME"
    FileResource="{x:Null}"
    InputEntity="{x:Null}"
    OutputEntity="{x:Null}"
    ContinueOnError="False"
    DisplayName="Upload File to ENTITY_NAME"
    EntityId="ENTITY_GUID"
    ExpansionDepth="2"
    Field="FILE_FIELD_NAME"
    FilePath="C:\path\to\file.pdf"
    RecordId="[recordIdVariable]"
    TimeoutInMs="30000" />
```

- `Field` — bare string, not expression-wrapped. Use the field name exactly as it appears in `EntitiesStore.json`
- `FilePath` — bare string for literal paths. Use expression syntax (`[variableName]`) only when the path comes from a variable
- When using `FilePath`, set `FileResource="{x:Null}"`
- Studio explicitly serializes unused nullable properties as `{x:Null}` — include them for properties that exist on the activity (do not include `ScopeValue`/`SolutionEntityKey`/`SolutionEntityName` in standalone projects)

## XAML Example — Upload from FileResource (Round-Trip)

```xml
<uda:UploadFileToRecordField
    x:TypeArguments="local:ENTITY_NAME"
    FilePath="{x:Null}"
    InputEntity="{x:Null}"
    OutputEntity="{x:Null}"
    ContinueOnError="False"
    DisplayName="Upload File to ENTITY_NAME"
    EntityId="ENTITY_GUID"
    ExpansionDepth="2"
    Field="FILE_FIELD_NAME"
    FileResource="[downloadedFileResource]"
    RecordId="[recordIdVariable]"
    TimeoutInMs="30000" />
```

- When using `FileResource`, set `FilePath="{x:Null}"`
- `downloadedFileResource` is typed as `upr:ILocalResource` (`UiPath.Platform.ResourceHandling.ILocalResource`) — the output of `DownloadFileFromRecordField.DownloadedFileResource`
- `ILocalResource` is assignment-compatible with `IResource` (the `FileResource` input type) — no cast needed
- **This is the preferred pattern for round-trip file copies** — it preserves the original filename. See [DownloadFileFromRecordField — Round-Trip Pattern](DownloadFileFromRecordField.md#round-trip-pattern-download--upload)

## When to Use FilePath vs FileResource

| Scenario | Use | Set the other to |
|----------|-----|-----------------|
| File comes from another activity in the same workflow (e.g., `DownloadFileFromRecordField`) | `FileResource="[downloadedFileResource]"` | `FilePath="{x:Null}"` |
| File is at a known path on disk (user-specified or hardcoded) | `FilePath="C:\path\to\file.pdf"` | `FileResource="{x:Null}"` |

**Never fabricate a temp file path** to bridge two activities. If the file originates from `DownloadFileFromRecordField`, chain via `FileResource` — it preserves the original filename. Fabricated paths (e.g., `"C:\temp\file_" & guid & ".pdf"`) lose the filename and create cleanup obligations.

## Key Rules

- **Maximum file size is 10 MB.** Uploads larger than 10 MB are rejected by the Data Service API at runtime — split or compress before calling this activity
- Either `FilePath` or `FileResource` must be provided — if both are `{x:Null}`, validation fails
- **Prefer `FileResource` for round-trip file copies** — pass the `ILocalResource` from download directly; this preserves the original filename
- If `FileResource` is provided, it is resolved to a local path at runtime via `ToLocalResource().ResolveAsync()`
- The `Field` property must match a field with `FieldDisplayType: "File"` in `EntitiesStore.json`
- `Field` and `FilePath` accept bare strings for literal values — do not wrap in expression brackets (`[...]`) unless the value comes from a variable
