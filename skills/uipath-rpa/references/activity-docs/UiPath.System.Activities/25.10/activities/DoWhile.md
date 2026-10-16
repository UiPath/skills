# Do While

Executes body first, then checks condition. No namespace prefix.

```xml
<DoWhile DisplayName="Do While">
  <DoWhile.Condition>
    <CSharpValue x:TypeArguments="x:Boolean">retryCount &lt; 3</CSharpValue>
  </DoWhile.Condition>
  <Sequence DisplayName="Do Body">
    <!-- Activities to repeat (executed at least once) -->
  </Sequence>
</DoWhile>
```

**Key rules:**
- Condition is an `Activity<bool>`: the expression goes directly inside `<DoWhile.Condition>`, with no `<InArgument>` wrapper. The wrapped form fails to load.
