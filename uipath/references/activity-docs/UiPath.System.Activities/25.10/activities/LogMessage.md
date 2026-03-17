# Log Message

Writes to the UiPath execution log. Uses `ui:` namespace prefix.

```xml
<!-- Simple string message -->
<ui:LogMessage DisplayName="Log Message" Level="Info">
  <ui:LogMessage.Message>
    <InArgument x:TypeArguments="x:Object">
      <CSharpValue x:TypeArguments="x:Object">"Processing started"</CSharpValue>
    </InArgument>
  </ui:LogMessage.Message>
</ui:LogMessage>

<!-- Expression with variable interpolation -->
<ui:LogMessage DisplayName="Log Status" Level="Warn">
  <ui:LogMessage.Message>
    <InArgument x:TypeArguments="x:Object">
      <CSharpValue x:TypeArguments="x:Object">"Processed " + count.ToString() + " items"</CSharpValue>
    </InArgument>
  </ui:LogMessage.Message>
</ui:LogMessage>
```

**Key rules:**
- Message type is always `x:Object` (not `x:String`) — accepts any expression
- `Level` attribute: `Trace`, `Info`, `Warn`, `Error`, `Fatal` (default: `Info`)
- String interpolation: use C# string concatenation (`+`), not `$""` interpolation (XAML doesn't support it)
