# Switch

Multi-branch based on an expression value. No namespace prefix.

```xml
<Switch x:TypeArguments="x:String" DisplayName="Switch on Status">
  <Switch.Expression>
    <InArgument x:TypeArguments="x:String">
      <CSharpValue x:TypeArguments="x:String">status</CSharpValue>
    </InArgument>
  </Switch.Expression>
  <Switch.Default>
    <Sequence DisplayName="Default">
      <ui:LogMessage DisplayName="Log Unknown">
        <ui:LogMessage.Message>
          <InArgument x:TypeArguments="x:Object">
            <CSharpValue x:TypeArguments="x:Object">"Unknown status"</CSharpValue>
          </InArgument>
        </ui:LogMessage.Message>
      </ui:LogMessage>
    </Sequence>
  </Switch.Default>
  <x:String x:Key="Active">
    <Sequence DisplayName="Active Case">
      <!-- Activities for "Active" -->
    </Sequence>
  </x:String>
  <x:String x:Key="Inactive">
    <Sequence DisplayName="Inactive Case">
      <!-- Activities for "Inactive" -->
    </Sequence>
  </x:String>
</Switch>
```

**Key rules:**
- `x:TypeArguments` must match the switch expression type
- Case keys use `x:Key` attribute with the matching value
- `Switch.Default` is optional but recommended
- For `x:Int32` switch: use `<x:Int32 x:Key="1">...</x:Int32>` etc.
