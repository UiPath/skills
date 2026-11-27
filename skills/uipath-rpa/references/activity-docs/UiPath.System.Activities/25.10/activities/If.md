# If / Else

Conditional branching. No namespace prefix.

```xml
<If DisplayName="Check Condition">
  <If.Condition>
    <InArgument x:TypeArguments="x:Boolean">
      <CSharpValue x:TypeArguments="x:Boolean">myValue &gt; 10</CSharpValue>
    </InArgument>
  </If.Condition>
  <If.Then>
    <Sequence DisplayName="Then">
      <!-- Activities when condition is true -->
    </Sequence>
  </If.Then>
  <If.Else>
    <Sequence DisplayName="Else">
      <!-- Activities when condition is false -->
    </Sequence>
  </If.Else>
</If>
```

**Key rules:**
- Condition is always `InArgument x:TypeArguments="x:Boolean"` — expression must evaluate to bool
- `If.Then` and `If.Else` each wrap content in a `<Sequence>` — even for a single activity. Studio's designer expects the wrap as a drop zone.
- `If.Else` is optional (can be omitted for if-without-else)
