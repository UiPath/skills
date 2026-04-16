# DeleteFileFromRecordField

Deletes a file attachment from a file-type field on an entity record. Category: **DataService.File**.

## Properties

| Property | Type | Required | Default | Category | Description |
|----------|------|----------|---------|----------|-------------|
| `x:TypeArguments` | — | Yes | — | — | Concrete entity type: `local:EntityName` |
| `EntityId` | `InArgument<Guid>` | Yes | — | — | Entity GUID from `EntitiesStore.json` |
| `RecordId` | `InArgument<Guid>` | Yes | — | Input | GUID of the target record (`[RequiredArgument]`) |
| `Field` | `InArgument<string>` | Yes | — | Input | Name of the file field (`[RequiredArgument]`, `[Browsable(false)]`) |
| `ExpansionDepth` | `InArgument<int>` | No | `2` | Options | Depth of relationship expansion in response (range: 1–3) |
| `OutputEntity` | `OutArgument<TEntity>` | No | — | Output | Receives the updated entity after file deletion |
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Common | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Common | Timeout in milliseconds |

## XAML Example

```xml
<uda:DeleteFileFromRecordField
    x:TypeArguments="local:ENTITY_NAME"
    ContinueOnError="False"
    DisplayName="Delete File from ENTITY_NAME"
    EntityId="ENTITY_GUID"
    RecordId="[recordIdVariable]"
    Field="[&quot;FileFieldName&quot;]"
    ExpansionDepth="2"
    OutputEntity="[updatedEntity]"
    TimeoutInMs="30000" />
```
