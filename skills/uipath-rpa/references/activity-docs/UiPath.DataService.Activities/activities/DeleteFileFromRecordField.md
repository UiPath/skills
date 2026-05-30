# Delete File From Record Field

`UiPath.DataService.Activities.DeleteFileFromRecordField<TEntity>`

**Package:** `UiPath.DataService.Activities`

Deletes a file attachment from a file-type field on an entity record.

**Category:** Data Service.File

## Properties

| Property | Type | Required | Default | Category | Description |
|----------|------|----------|---------|----------|-------------|
| `x:TypeArguments` | — | Yes | — | — | Concrete entity type: `local:EntityName` |
| `EntityId` | `InArgument<Guid>` | Yes | — | — | Entity GUID from `EntitiesStore.json` |
| `RecordId` | `InArgument<Guid>` | Yes | — | Input | GUID of the target record (`[RequiredArgument]`) |
| `Field` | `InArgument<string>` | Yes | — | Input | Name of the file field (`[RequiredArgument]`, `[Browsable(false)]`) |
| `ExpansionDepth` | `InArgument<int>` | No | `2` | Options | Depth of relationship expansion on the returned entity (range: 1–3, max `3`) — see [overview § Relationship Fields & ExpansionDepth](../overview.md#relationship-fields--expansiondepth) |
| `OutputEntity` | `OutArgument<TEntity>` | No | — | Output | Receives the updated entity after file deletion |
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Common | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Common | Timeout in milliseconds |

> **Solution scope properties** (`ScopeValue`, `SolutionEntityKey`, `SolutionEntityName`) only apply when the project has a SolutionId. For standalone projects, **omit these properties entirely** — the members do not exist on the activity in standalone scope. See [overview — Solution Scope Properties](overview.md#solution-scope-properties-conditional) and [Solution Context](overview.md#solution-context-folder-vs-tenant-scope).

## XAML Example

```xml
<uda:DeleteFileFromRecordField
    x:TypeArguments="local:ENTITY_NAME"
    InputEntity="{x:Null}"
    OutputEntity="{x:Null}"
    ContinueOnError="False"
    DisplayName="Delete File from ENTITY_NAME"
    EntityId="ENTITY_GUID"
    ExpansionDepth="2"
    Field="FILE_FIELD_NAME"
    RecordId="[recordIdVariable]"
    TimeoutInMs="30000" />
```

- `Field` — bare string, not expression-wrapped. Use the field name exactly as it appears in `EntitiesStore.json`
- Studio explicitly serializes unused nullable properties as `{x:Null}` — include `InputEntity`, `OutputEntity` (do not include `ScopeValue`/`SolutionEntityKey`/`SolutionEntityName` in standalone projects — the members do not exist on the activity)
