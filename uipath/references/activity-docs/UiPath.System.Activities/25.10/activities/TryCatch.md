# Try Catch

Error handling. No namespace prefix.

```xml
<TryCatch DisplayName="Try Catch">
  <TryCatch.Try>
    <Sequence DisplayName="Try">
      <!-- Activities that may throw -->
    </Sequence>
  </TryCatch.Try>
  <TryCatch.Catches>
    <Catch x:TypeArguments="s:Exception">
      <ActivityAction x:TypeArguments="s:Exception">
        <ActivityAction.Argument>
          <DelegateInArgument x:TypeArguments="s:Exception" Name="exception" />
        </ActivityAction.Argument>
        <Sequence DisplayName="Catch">
          <ui:LogMessage DisplayName="Log Error" Level="Error">
            <ui:LogMessage.Message>
              <InArgument x:TypeArguments="x:Object">
                <CSharpValue x:TypeArguments="x:Object">exception.Message</CSharpValue>
              </InArgument>
            </ui:LogMessage.Message>
          </ui:LogMessage>
        </Sequence>
      </ActivityAction>
    </Catch>
  </TryCatch.Catches>
  <TryCatch.Finally>
    <Sequence DisplayName="Finally">
      <!-- Cleanup activities (always runs) -->
    </Sequence>
  </TryCatch.Finally>
</TryCatch>
```

**Key rules:**
- `Catch x:TypeArguments` specifies the exception type — `s:Exception` catches all
- The `DelegateInArgument` `Name` is the exception variable (usable in the Catch body)
- Can have multiple `<Catch>` blocks for different exception types
- `TryCatch.Finally` is optional
- `s:` prefix requires `xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"`
