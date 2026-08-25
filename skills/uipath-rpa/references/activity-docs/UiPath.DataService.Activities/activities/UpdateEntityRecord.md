# Update Entity Record

`UiPath.DataService.Activities.UpdateEntityRecord<TEntity>`

**Package:** `UiPath.DataService.Activities`

Updates an existing record in a Data Fabric entity.

**Category:** Data Service.Entity Record

> **Single vs batch — use this only for ONE record.** For N records (each entity object pre-populated with its `Id`), use [UpdateMultipleEntityRecords](UpdateMultipleEntityRecords.md) — one HTTP request and partial-batch failure reporting via `FailedRecords`. Updating inside a `ForEach` loop is a performance anti-pattern. Full decision guide: [overview — When to Use Batch vs Single-Record Activities](../overview.md#when-to-use-batch-vs-single-record-activities).

## Properties

`x:TypeArguments` — concrete entity type, e.g. `local:EntityName`. Required at activity declaration.

### Input

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `EntityId` | `InArgument<Guid>` | Yes | — | Entity GUID from `EntitiesStore.json` |
| `RecordId` | `InArgument<Guid>` | Yes | — | GUID of the record to update |
| `InputEntityInFieldView` | `InArgument<TEntity>` | Yes | — | Object-initializer expression with updated field values (runtime reads this) |
| `InputEntity` | `InArgument<TEntity>` | No | — | Not recommended — Studio never syncs `SelectedFields` to this property, causing desync |
| `State` | `RecordState` | Yes | — | Contains `SelectedFields` with field GUIDs and values (Studio card UI reads this) |
| `ExpansionDepth` | `InArgument<int>` | No | `2` | Depth of relationship expansion in response (range: 1–3, max `3`). On write, relationship fields take **only** the target record's Id GUID — see [overview § Relationship Fields & ExpansionDepth](../overview.md#relationship-fields--expansiondepth) |

### Output

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `OutputEntity` | `OutArgument<TEntity>` | No | — | Receives the updated record |

### Configuration

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `IsInRecordView` | `InArgument<bool>` | Yes | — | Set to `[False]` — makes runtime read `InputEntityInFieldView` |
| `VisibleDynamicPropertiesInfo` | `InArgument<string>` | No | `{x:Null}` | Always set to `{x:Null}` |

### Common

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Timeout in milliseconds |

> **Solution scope properties** (`ScopeValue`, `SolutionEntityKey`, `SolutionEntityName`) only apply when the project has a SolutionId. For standalone projects, omit them. See [overview — Solution Scope Properties](../overview.md#solution-scope-properties-conditional) and [Solution Context](../overview.md#solution-context-folder-vs-tenant-scope).

## Field Binding — Two Required Components

For Create and Update activities, set `IsInRecordView="[False]"` and populate two things:

1. **`InputEntityInFieldView`** — object-initializer expression with updated field values. The runtime evaluates this expression and sends it to the Data Service API.
2. **`State` with `RecordState.SelectedFields`** — declares each field with its GUID from `EntitiesStore.json` and its value. Studio's card UI reads this to render per-field editors.

Studio syncs `SelectedFields` → `InputEntityInFieldView` on file load, keeping them aligned. Do NOT use `InputEntity` — Studio never syncs `SelectedFields` to it, which causes the card UI to show one value while the runtime uses a stale one.

## RecordState and DynamicEntityField

`RecordState` properties:

| Property | Type | Description |
|----------|------|-------------|
| `IsInRecordView` | `bool` | Set to `False` |
| `RequiredFieldCount` | `int` | Count of `DynamicEntityField` entries where `IsRequired="True"` |
| `SelectedFields` | `IList<DynamicEntityField>` | List of field declarations |

`DynamicEntityField` properties:

| Property | Type | Description |
|----------|------|-------------|
| `Id` | `Guid` | Field GUID from `EntitiesStore.json` → `Fields[].Id` |
| `Name` | `string` | Field name from `EntitiesStore.json` → `Fields[].Name` |
| `IsRequired` | `bool` | Whether the field is required |
| `ArgumentValue` | `Argument` | The value as `InArgument` with appropriate `x:TypeArguments` |

## XAML Example (VB.NET expression language)

> This snippet uses the `udam:` prefix (`RecordState`, `DynamicEntityField`). Ensure `xmlns:udam` is declared on the root `<Activity>` element — see [overview — XAML Namespace Declarations](../overview.md#xaml-namespace-declarations).

```xml
<uda:UpdateEntityRecord
    x:TypeArguments="local:ENTITY_NAME"
    OutputEntity="{x:Null}"
    VisibleDynamicPropertiesInfo="{x:Null}"
    ContinueOnError="False"
    DisplayName="Update ENTITY_NAME Record"
    EntityId="ENTITY_GUID"
    ExpansionDepth="2"
    RecordId="[recordIdVariable]"
    InputEntityInFieldView="[New ENTITY_NAME() With {.FIELD_A = &quot;newValue&quot;}]"
    IsInRecordView="[False]"
    TimeoutInMs="30000">
  <uda:UpdateEntityRecord.State>
    <udam:RecordState IsInRecordView="False" RequiredFieldCount="0">
      <udam:RecordState.SelectedFields>
        <scg:List x:TypeArguments="udam:DynamicEntityField">
          <udam:DynamicEntityField Id="FIELD_A_GUID" IsRequired="False" Name="FIELD_A">
            <udam:DynamicEntityField.ArgumentValue>
              <InArgument x:TypeArguments="x:String">[&quot;newValue&quot;]</InArgument>
            </udam:DynamicEntityField.ArgumentValue>
          </udam:DynamicEntityField>
        </scg:List>
      </udam:RecordState.SelectedFields>
    </udam:RecordState>
  </uda:UpdateEntityRecord.State>
</uda:UpdateEntityRecord>
```

Replace: `ENTITY_NAME` (entity class), `ENTITY_GUID` (from `EntitiesStore.json` → `Entities[].Id`), `FIELD_A` (field name), `FIELD_A_GUID` (from `Fields[].Id`).

## Key Rules

- Set `IsInRecordView="[False]"` and populate both `InputEntityInFieldView` and `RecordState.SelectedFields` — do NOT use `InputEntity`
- At least one field in `SelectedFields` must have an `ArgumentValue` set — otherwise validation fails with "No update fields specified"
- If the `InputEntityInFieldView` expression does not set `Id`, the activity copies `RecordId` into the entity automatically at runtime
- Only include fields you want to update in `SelectedFields` and `InputEntityInFieldView` — unchanged fields can be omitted
- `VisibleDynamicPropertiesInfo` must always be set to `{x:Null}` — the type `DynamicPropertiesInfo` is not public
- Entity fields cannot be set as direct activity properties — `<uda:UpdateEntityRecord.FieldName>` produces `Cannot set unknown member`
