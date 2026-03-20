# For Each

Iterates over a collection. Uses `ui:` namespace prefix. The `x:TypeArguments` on the `ForEach` element specifies the **item type**.

```xml
<!-- ForEach over strings -->
<ui:ForEach x:TypeArguments="x:String" DisplayName="For Each item">
  <ui:ForEach.Values>
    <InArgument x:TypeArguments="sc:IEnumerable">
      <CSharpValue x:TypeArguments="sc:IEnumerable">myStringList</CSharpValue>
    </InArgument>
  </ui:ForEach.Values>
  <ui:ForEach.Body>
    <ActivityAction x:TypeArguments="x:String">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="x:String" Name="item" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Body">
        <!-- Use "item" variable here -->
        <ui:LogMessage DisplayName="Log Item">
          <ui:LogMessage.Message>
            <InArgument x:TypeArguments="x:Object">
              <CSharpValue x:TypeArguments="x:Object">item</CSharpValue>
            </InArgument>
          </ui:LogMessage.Message>
        </ui:LogMessage>
      </Sequence>
    </ActivityAction>
  </ui:ForEach.Body>
</ui:ForEach>

<!-- ForEach over integers -->
<ui:ForEach x:TypeArguments="x:Int32" DisplayName="For Each number">
  <ui:ForEach.Values>
    <InArgument x:TypeArguments="sc:IEnumerable">
      <CSharpValue x:TypeArguments="sc:IEnumerable">Enumerable.Range(0, 10)</CSharpValue>
    </InArgument>
  </ui:ForEach.Values>
  <ui:ForEach.Body>
    <ActivityAction x:TypeArguments="x:Int32">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="x:Int32" Name="num" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Body">
        <!-- Use "num" variable here -->
      </Sequence>
    </ActivityAction>
  </ui:ForEach.Body>
</ui:ForEach>
```

**Key rules:**
- `x:TypeArguments` on `ui:ForEach`, `ActivityAction`, and `DelegateInArgument` must ALL match the item type
- `ForEach.Values` is always `InArgument x:TypeArguments="sc:IEnumerable"` regardless of item type
- The `DelegateInArgument` `Name` is the loop variable name — usable inside the Body
- Body must contain exactly **one** activity — wrap multiple activities in a `<Sequence>`
- `CurrentIndex="{x:Null}"` is optional (stores current iteration index if set to a variable)
