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
  <Sequence x:Key="Active" DisplayName="Active Case">
    <!-- Activities for "Active" -->
  </Sequence>
  <Sequence x:Key="Inactive" DisplayName="Inactive Case">
    <!-- Activities for "Inactive" -->
  </Sequence>
</Switch>
```

**Key rules:**
- `x:TypeArguments` must match the switch expression type
- Each case is a `Sequence` carrying `x:Key="<literal>"` directly inside `<Switch>`; wrap every case and `Switch.Default` in a `Sequence`, even for a single activity (Rule 24)
- `Switch.Default` is optional but recommended
- For `x:Int32` switch: set `x:TypeArguments="x:Int32"` on `<Switch>`, its `Switch.Expression` `InArgument`, and the expression value, then key cases as `<Sequence x:Key="1" ...>`
