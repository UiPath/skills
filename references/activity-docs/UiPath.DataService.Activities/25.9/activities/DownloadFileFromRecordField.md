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

## Key Rules

- `DownloadedFileResource` returns an `ILocalResource` with the local file path — use `.LocalPath` to get the path
- If `FilePath` is specified, the file is saved to that location; otherwise a temporary location is used
