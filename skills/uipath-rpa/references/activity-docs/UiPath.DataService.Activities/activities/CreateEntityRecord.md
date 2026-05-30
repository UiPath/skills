# Create Entity Record

`UiPath.DataService.Activities.CreateEntityRecord<TEntity>`

**Package:** `UiPath.DataService.Activities`

Creates a new record in a Data Fabric entity.

**Category:** Data Service.Entity Record

> **Single vs batch — use this only for ONE record.** For N records collected at runtime, use [CreateMultipleEntityRecords](CreateMultipleEntityRecords.md) — one HTTP request and per-record failure reporting via `FailedRecords`. Calling `CreateEntityRecord` inside a `ForEach` is a known performance anti-pattern. Full decision guide: [overview — When to Use Batch vs Single-Record Activities](../overview.md#when-to-use-batch-vs-single-record-activities).

## Properties

| Property | Type | Required | Default | Category | Description |
|----------|------|----------|---------|----------|-------------|
| `x:TypeArguments` | — | Yes | — | — | Concrete entity type: `local:EntityName` |
| `EntityId` | `InArgument<Guid>` | Yes | — | — | Entity GUID from `EntitiesStore.json` |
| `InputEntityInFieldView` | `InArgument<TEntity>` | Yes | — | Input | Object-initializer expression constructing the entity (runtime reads this) |
| `IsInRecordView` | `InArgument<bool>` | Yes | — | — | Set to `[False]` — makes runtime read `InputEntityInFieldView` |
| `State` | `RecordState` | Yes | — | — | Contains `SelectedFields` with field GUIDs and values (Studio card UI reads this) |
| `InputEntity` | `InArgument<TEntity>` | No | — | Input | Not recommended — Studio never syncs `SelectedFields` to this property, causing desync |
| `VisibleDynamicPropertiesInfo` | `InArgument<string>` | No | `{x:Null}` | — | Always set to `{x:Null}` |
| `ExpansionDepth` | `InArgument<int>` | No | `2` | Options | Depth of relationship expansion in response (range: 1–3, max `3`). On write, relationship fields take **only** the target record's Id GUID — see [overview § Relationship Fields & ExpansionDepth](../overview.md#relationship-fields--expansiondepth) |
| `OutputEntity` | `OutArgument<TEntity>` | No | — | Output | Receives the created record with server-assigned ID |
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Common | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Common | Timeout in milliseconds |

> **Solution scope properties** (`ScopeValue`, `SolutionEntityKey`, `SolutionEntityName`) only apply when the project has a SolutionId. For standalone projects, omit them. See [overview — Solution Scope Properties](overview.md#solution-scope-properties-conditional) and [Solution Context](overview.md#solution-context-folder-vs-tenant-scope).

## Field Binding — Two Required Components

For Create and Update activities, set `IsInRecordView="[False]"` and populate two things:

1. **`InputEntityInFieldView`** — object-initializer expression constructing the entity with field values. The runtime evaluates this expression and sends it to the Data Service API.
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

> This snippet uses the `udam:` prefix (`RecordState`, `DynamicEntityField`). Ensure `xmlns:udam` is declared on the root `<Activity>` element — see [overview — XAML Namespace Declarations](overview.md#xaml-namespace-declarations).

```xml
<uda:CreateEntityRecord
    x:TypeArguments="local:ENTITY_NAME"
    OutputEntity="{x:Null}"
    VisibleDynamicPropertiesInfo="{x:Null}"
    ContinueOnError="False"
    DisplayName="Create ENTITY_NAME Record"
    EntityId="ENTITY_GUID"
    ExpansionDepth="2"
    InputEntityInFieldView="[New ENTITY_NAME() With {.FIELD_A = &quot;valueA&quot;, .FIELD_B = 42}]"
    IsInRecordView="[False]"
    TimeoutInMs="30000">
  <uda:CreateEntityRecord.State>
    <udam:RecordState IsInRecordView="False" RequiredFieldCount="REQUIRED_COUNT">
      <udam:RecordState.SelectedFields>
        <scg:List x:TypeArguments="udam:DynamicEntityField">
          <udam:DynamicEntityField Id="FIELD_A_GUID" IsRequired="True" Name="FIELD_A">
            <udam:DynamicEntityField.ArgumentValue>
              <InArgument x:TypeArguments="x:String">[&quot;valueA&quot;]</InArgument>
            </udam:DynamicEntityField.ArgumentValue>
          </udam:DynamicEntityField>
          <udam:DynamicEntityField Id="FIELD_B_GUID" IsRequired="False" Name="FIELD_B">
            <udam:DynamicEntityField.ArgumentValue>
              <InArgument x:TypeArguments="x:Int32">[42]</InArgument>
            </udam:DynamicEntityField.ArgumentValue>
          </udam:DynamicEntityField>
        </scg:List>
      </udam:RecordState.SelectedFields>
    </udam:RecordState>
  </uda:CreateEntityRecord.State>
</uda:CreateEntityRecord>
```

Replace: `ENTITY_NAME` (entity class), `ENTITY_GUID` (from `EntitiesStore.json` → `Entities[].Id`), `FIELD_A`/`FIELD_B` (field names), `FIELD_A_GUID`/`FIELD_B_GUID` (from `Fields[].Id`), `REQUIRED_COUNT` (count of required fields).

## Key Rules

- Set `IsInRecordView="[False]"` and populate both `InputEntityInFieldView` and `RecordState.SelectedFields` — do NOT use `InputEntity`
- Include every required non-system field (`IsRequired: true` AND `IsSystemField: false`) in both `SelectedFields` and the `InputEntityInFieldView` expression — omitting a required field fails validation
- `RequiredFieldCount` must equal the count of `DynamicEntityField` entries with `IsRequired="True"`
- **Empty records are valid.** If the entity has no required non-system fields, use `RequiredFieldCount="0"` with an empty `SelectedFields` list (`Capacity="0"`), and `InputEntityInFieldView="[New ENTITY_NAME()]"` with no field initializers. This is common for entities with only a file-type field or all-optional fields
- `VisibleDynamicPropertiesInfo` must always be set to `{x:Null}` — the type `DynamicPropertiesInfo` is not public
- Entity fields cannot be set as direct activity properties — `<uda:CreateEntityRecord.FieldName>` produces `Cannot set unknown member`

## XAML Example — Empty Record (No Required Fields)

```xml
<uda:CreateEntityRecord
    x:TypeArguments="local:ENTITY_NAME"
    OutputEntity="{x:Null}"
    VisibleDynamicPropertiesInfo="{x:Null}"
    ContinueOnError="False"
    DisplayName="Create Empty ENTITY_NAME Record"
    EntityId="ENTITY_GUID"
    ExpansionDepth="2"
    InputEntityInFieldView="[New ENTITY_NAME()]"
    IsInRecordView="[False]"
    TimeoutInMs="30000">
  <uda:CreateEntityRecord.State>
    <udam:RecordState IsInRecordView="False" RequiredFieldCount="0">
      <udam:RecordState.SelectedFields>
        <scg:List x:TypeArguments="udam:DynamicEntityField" Capacity="0" />
      </udam:RecordState.SelectedFields>
    </udam:RecordState>
  </uda:CreateEntityRecord.State>
</uda:CreateEntityRecord>
```

Use this pattern for entities where all non-system fields are optional (e.g., a file-only entity where the file is uploaded separately via `UploadFileToRecordField`).
