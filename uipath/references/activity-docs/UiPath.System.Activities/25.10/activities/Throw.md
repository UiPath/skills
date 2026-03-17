# Throw / Rethrow

Throw an exception. No namespace prefix.

```xml
<!-- Throw a new exception -->
<Throw DisplayName="Throw Error">
  <Throw.Exception>
    <InArgument x:TypeArguments="s:Exception">
      <CSharpValue x:TypeArguments="s:Exception">new Exception("Something went wrong")</CSharpValue>
    </InArgument>
  </Throw.Exception>
</Throw>

<!-- Rethrow (only valid inside a Catch block) -->
<Rethrow DisplayName="Rethrow" />
```
