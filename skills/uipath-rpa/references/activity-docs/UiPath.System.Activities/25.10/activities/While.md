# While

Repeats while condition is true. No namespace prefix.

```xml
<While DisplayName="While Processing">
  <While.Condition>
    <CSharpValue x:TypeArguments="x:Boolean">counter &lt; maxItems</CSharpValue>
  </While.Condition>
  <Sequence DisplayName="While Body">
    <!-- Activities to repeat -->
  </Sequence>
</While>
```

**Key rules:**
- Condition is an `Activity<bool>`: the expression goes directly inside `<While.Condition>`, with no `<InArgument>` wrapper — unlike If, whose Condition is an `InArgument<bool>`. The wrapped form fails to load (`Set property 'System.Activities.Statements.While.Condition' threw an exception`)
- Body wraps in `<Sequence>` — even for a single activity. Studio's designer expects the wrap as a drop zone.
- Remember XML escaping: `<` → `&lt;`, `>` → `&gt;`, `&` → `&amp;`
