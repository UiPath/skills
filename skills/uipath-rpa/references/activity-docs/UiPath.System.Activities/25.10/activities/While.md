# While

Repeats while condition is true. No namespace prefix.

```xml
<While DisplayName="While Processing">
  <While.Condition>
    <InArgument x:TypeArguments="x:Boolean">
      <CSharpValue x:TypeArguments="x:Boolean">counter &lt; maxItems</CSharpValue>
    </InArgument>
  </While.Condition>
  <Sequence DisplayName="While Body">
    <!-- Activities to repeat -->
  </Sequence>
</While>
```

**Key rules:**
- Condition is `InArgument x:TypeArguments="x:Boolean"` — same as If
- Body wraps in `<Sequence>` — even for a single activity. Studio's designer expects the wrap as a drop zone.
- Remember XML escaping: `<` → `&lt;`, `>` → `&gt;`, `&` → `&amp;`
