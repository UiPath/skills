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

> **Solution scope.** When this activity sits in a project with a non-empty `SolutionId`, Studio renders a Folder/Tenant radio plus an entity picker — not the three raw XAML properties. Folder scope writes `ScopeValue="Folder"`, `SolutionEntityKey` (resource UUID, design-time only) and `SolutionEntityName` (binding key + display name); at runtime the activity reads `Entity.<SolutionEntityName>.folderPath` from `bindings_v2.json` → Orchestrator's `resourceOverwrites` and injects `X-UiPath-FolderPath`. Tenant scope leaves the three properties unset. See [overview — Solution Context](../overview.md#solution-context-folder-vs-tenant-scope).

No `ExpansionDepth` — download returns a file, not an entity.

## XAML Example

```xml
<uda:DownloadFileFromRecordField
    x:TypeArguments="local:ENTITY_NAME"
    FilePath="{x:Null}"
    ContinueOnError="False"
    DisplayName="Download File from ENTITY_NAME"
    DownloadedFileResource="[downloadedFileResource]"
    EntityId="ENTITY_GUID"
    Field="FILE_FIELD_NAME"
    RecordId="[recordIdVariable]"
    TimeoutInMs="30000" />
```

- `Field` — bare string, not expression-wrapped. Use the field name exactly as it appears in `EntitiesStore.json`
- `FilePath` — set to `{x:Null}` when using `DownloadedFileResource` (preferred). If saving to a specific path, use a bare string: `FilePath="C:\downloads\output.pdf"`
- Studio explicitly serializes unused nullable properties as `{x:Null}` — include them for properties that exist on the activity (do not include `ScopeValue`/`SolutionEntityKey`/`SolutionEntityName` in standalone projects)

### Variable Declaration

```xml
<Variable x:TypeArguments="upr:ILocalResource" Name="downloadedFileResource" />
```

Requires `xmlns:upr="clr-namespace:UiPath.Platform.ResourceHandling;assembly=UiPath.Platform"` on the root `<Activity>` element. See [overview — XAML Namespace Declarations](../overview.md#xaml-namespace-declarations).

## Round-Trip Pattern (Download → Upload)

When copying a file between records, chain `DownloadedFileResource` directly into `UploadFileToRecordField.FileResource`. This preserves the original filename and avoids fabricating temp paths.

```xml
<!-- Step 1: Download — capture DownloadedFileResource, set FilePath to {x:Null} -->
<uda:DownloadFileFromRecordField
    x:TypeArguments="local:ENTITY_NAME"
    FilePath="{x:Null}"
    ContinueOnError="False"
    DisplayName="Download File"
    DownloadedFileResource="[downloadedFileResource]"
    EntityId="ENTITY_GUID"
    Field="FILE_FIELD_NAME"
    RecordId="[sourceRecordId]"
    TimeoutInMs="30000" />

<!-- Step 2: Upload — pass downloadedFileResource as FileResource, set FilePath to {x:Null} -->
<uda:UploadFileToRecordField
    x:TypeArguments="local:ENTITY_NAME"
    FilePath="{x:Null}"
    InputEntity="{x:Null}"
    OutputEntity="{x:Null}"
    ContinueOnError="False"
    DisplayName="Upload File"
    EntityId="ENTITY_GUID"
    ExpansionDepth="2"
    Field="FILE_FIELD_NAME"
    FileResource="[downloadedFileResource]"
    RecordId="[targetRecordId]"
    TimeoutInMs="30000" />
```

> **Prefer `FileResource` over `FilePath`** when the file originates from another activity. `ILocalResource` (from download, `UiPath.Platform.ResourceHandling`) is assignment-compatible with `IResource` (upload input) — no cast needed. Using `FilePath` with a fabricated temp path loses the original filename. The round-trip preserves it.

## When to Use FilePath vs DownloadedFileResource

| Scenario | Use | FilePath value |
|----------|-----|----------------|
| File will be consumed by another activity in the same workflow (e.g., upload to another record) | `DownloadedFileResource` | `{x:Null}` |
| File needs to be saved to a specific user-provided location | `FilePath` | Bare string path (e.g., `C:\downloads\output.pdf`) |
| Both — save to disk AND pass to another activity | Both | Set `FilePath` to the desired path; also capture `DownloadedFileResource` |

**Never fabricate a temp file path.** If you need a temporary location, omit `FilePath` (set `{x:Null}`) and use `DownloadedFileResource` — the runtime handles temp storage. Fabricated paths (e.g., `"C:\temp\file_" & guid & ".pdf"`) lose the original filename and create cleanup obligations.

## Key Rules

- `DownloadedFileResource` returns a `UiPath.Platform.ResourceHandling.ILocalResource` — use `.LocalPath` to get the file path
- If `FilePath` is specified, the file is saved to that location; otherwise a temporary location is used
- **For round-trip file copies, omit `FilePath` (set `{x:Null}`) and use `DownloadedFileResource` → `FileResource` chaining** — see pattern above
- `Field` and `FilePath` accept bare strings for literal values — do not wrap in expression brackets (`[...]`) unless the value comes from a variable
