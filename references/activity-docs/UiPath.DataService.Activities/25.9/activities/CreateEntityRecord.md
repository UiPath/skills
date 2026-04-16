# CreateEntityRecord

Creates a new record in a Data Fabric entity. Category: **DataService.Entity Record**.

## Properties

| Property | Type | Required | Default | Category | Description |
|----------|------|----------|---------|----------|-------------|
| `x:TypeArguments` | — | Yes | — | — | Concrete entity type: `local:EntityName` |
| `EntityId` | `InArgument<Guid>` | Yes | — | — | Entity GUID from `EntitiesStore.json` |
| `InputEntity` | `InArgument<TEntity>` | Yes | — | Input | Object-initializer expression constructing the entity |
| `IsInRecordView` | `InArgument<bool>` | Yes | — | — | Must be `[True]` when using record-view field binding |
| `State` | `RecordState` | Yes | — | — | Contains `SelectedFields` with field GUIDs and values |
| `InputEntityInFieldView` | `InArgument<TEntity>` | No | `{x:Null}` | Input | Alternative input for field-view mode |
| `VisibleDynamicPropertiesInfo` | `InArgument<string>` | No | `{x:Null}` | — | Always set to `{x:Null}` |
| `ExpansionDepth` | `InArgument<int>` | No | `2` | Options | Depth of relationship expansion in response (range: 1–3) |
| `OutputEntity` | `OutArgument<TEntity>` | No | — | Output | Receives the created record with server-assigned ID |
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Common | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Common | Timeout in milliseconds |

## Field Binding — Three Required Components

For Create and Update activities, **three things must be set together** or validation fails:

1. **`IsInRecordView="[True]"`** — tells the activity to use record-view field binding
2. **`InputEntity`** — an object-initializer expression that constructs the entity with field values
3. **`State` with `RecordState.SelectedFields`** — declares each field with its GUID from `EntitiesStore.json`

Omitting any one produces a clean parse but fails validation with "One or more required field is not set".

## RecordState and DynamicEntityField

`RecordState` properties:

| Property | Type | Description |
|----------|------|-------------|
| `IsInRecordView` | `bool` | Must be `True` |
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

```xml
<uda:CreateEntityRecord
    x:TypeArguments="local:ENTITY_NAME"
    InputEntityInFieldView="{x:Null}"
    OutputEntity="{x:Null}"
    VisibleDynamicPropertiesInfo="{x:Null}"
    ContinueOnError="False"
    DisplayName="Create ENTITY_NAME Record"
    EntityId="ENTITY_GUID"
    ExpansionDepth="2"
    InputEntity="[New ENTITY_NAME() With {.FIELD_A = &quot;valueA&quot;, .FIELD_B = 42}]"
    IsInRecordView="[True]"
    TimeoutInMs="30000">
  <uda:CreateEntityRecord.State>
    <udam:RecordState IsInRecordView="True" RequiredFieldCount="REQUIRED_COUNT">
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

- Include every required non-system field (`IsRequired: true` AND `IsSystemField: false`) in `SelectedFields` — omitting one fails validation
- `RequiredFieldCount` must equal the count of `DynamicEntityField` entries with `IsRequired="True"`
- `VisibleDynamicPropertiesInfo` must always be set to `{x:Null}` — the type `DynamicPropertiesInfo` is not public
- Entity fields cannot be set as direct activity properties — `<uda:CreateEntityRecord.FieldName>` produces `Cannot set unknown member`
