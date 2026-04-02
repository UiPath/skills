# Delay

Pauses execution. No namespace prefix.

```xml
<Delay DisplayName="Wait 5 Seconds">
  <Delay.Duration>
    <InArgument x:TypeArguments="s:TimeSpan">
      <CSharpValue x:TypeArguments="s:TimeSpan">TimeSpan.FromSeconds(5)</CSharpValue>
    </InArgument>
  </Delay.Duration>
</Delay>

<Delay DisplayName="Wait 1 Minute">
  <Delay.Duration>
    <InArgument x:TypeArguments="s:TimeSpan">
      <CSharpValue x:TypeArguments="s:TimeSpan">TimeSpan.FromMinutes(1)</CSharpValue>
    </InArgument>
  </Delay.Duration>
</Delay>
```
