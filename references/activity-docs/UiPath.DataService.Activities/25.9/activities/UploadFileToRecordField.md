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

## Key Rules

- Either `FilePath` or `FileResource` must be provided — if both are null, validation fails
- If `FileResource` is provided, it is resolved to a local path at runtime via `ToLocalResource().ResolveAsync()`
- The `Field` property must match a field with `FieldDisplayType: "File"` in `EntitiesStore.json`
