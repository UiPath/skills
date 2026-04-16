# UpdateEntityRecord

Updates an existing record in a Data Fabric entity. Category: **DataService.Entity Record**.

## Properties

| Property | Type | Required | Default | Category | Description |
|----------|------|----------|---------|----------|-------------|
| `x:TypeArguments` | — | Yes | — | — | Concrete entity type: `local:EntityName` |
| `EntityId` | `InArgument<Guid>` | Yes | — | — | Entity GUID from `EntitiesStore.json` |
| `RecordId` | `InArgument<Guid>` | Yes | — | Input | GUID of the record to update |
| `InputEntity` | `InArgument<TEntity>` | Yes | — | Input | Object-initializer expression with updated field values |
| `IsInRecordView` | `InArgument<bool>` | Yes | — | — | Must be `[True]` when using record-view field binding |
| `State` | `RecordState` | Yes | — | — | Contains `SelectedFields` with field GUIDs and values |
| `InputEntityInFieldView` | `InArgument<TEntity>` | No | `{x:Null}` | Input | Alternative input for field-view mode |
| `VisibleDynamicPropertiesInfo` | `InArgument<string>` | No | `{x:Null}` | — | Always set to `{x:Null}` |
| `ExpansionDepth` | `InArgument<int>` | No | `2` | Options | Depth of relationship expansion in response (range: 1–3) |
| `OutputEntity` | `OutArgument<TEntity>` | No | — | Output | Receives the updated record |
| `ContinueOnError` | `InArgument<bool>` | No | `false` | Common | Continue workflow on error |
| `TimeoutInMs` | `InArgument<int>` | No | `30000` | Common | Timeout in milliseconds |

## XAML Example (VB.NET expression language)

```xml
<uda:UpdateEntityRecord
    x:TypeArguments="local:ENTITY_NAME"
    InputEntityInFieldView="{x:Null}"
    OutputEntity="{x:Null}"
    VisibleDynamicPropertiesInfo="{x:Null}"
    ContinueOnError="False"
    DisplayName="Update ENTITY_NAME Record"
    EntityId="ENTITY_GUID"
    ExpansionDepth="2"
    RecordId="[recordIdVariable]"
    InputEntity="[New ENTITY_NAME() With {.FIELD_A = &quot;newValue&quot;}]"
    IsInRecordView="[True]"
    TimeoutInMs="30000">
  <uda:UpdateEntityRecord.State>
    <udam:RecordState IsInRecordView="True" RequiredFieldCount="0">
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

## Key Rules

- Same three-component field binding as `CreateEntityRecord`: `IsInRecordView` + `InputEntity` + `RecordState.SelectedFields`
- At least one field in `SelectedFields` must have an `ArgumentValue` set — otherwise validation fails with "No update fields specified"
- If the `InputEntity` expression does not set `Id`, the activity copies `RecordId` into the entity automatically at runtime
- Only include fields you want to update in `SelectedFields` — unchanged fields can be omitted
