# Do While

Executes body first, then checks condition. No namespace prefix.

```xml
<DoWhile DisplayName="Do While">
  <DoWhile.Condition>
    <InArgument x:TypeArguments="x:Boolean">
      <CSharpValue x:TypeArguments="x:Boolean">retryCount &lt; 3</CSharpValue>
    </InArgument>
  </DoWhile.Condition>
  <Sequence DisplayName="Do Body">
    <!-- Activities to repeat (executed at least once) -->
  </Sequence>
</DoWhile>
```
