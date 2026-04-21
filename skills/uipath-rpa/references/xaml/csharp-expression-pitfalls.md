# C# Expression Pitfalls

Failure modes specific to XAML expressions in C# projects (`expressionLanguage: CSharp`). Both pass static `get-errors` validation — they only fail at `CacheMetadata` time under `build` or `run-file`.

For the canonical binding form per property, see [csharp-activity-binding-guide.md](csharp-activity-binding-guide.md).

## Attribute-form expressions fail at runtime

Any non-literal attribute value on an `InArgument<T>` / `OutArgument<T>` property (e.g. `Message="logMessage"`, `TextString="statusText"`) is deserialized as `VisualBasicValue<T>` by the XAML attribute parser — regardless of the project's expression language. On non-Legacy projects the VB JIT is disabled, so these fail at runtime:

```
System.InvalidOperationException: JIT compilation is disabled for non-Legacy projects.
ExpressionToCompile { Code = "logMessage" ... } should have been compiled by the Studio Compiler.
```

**Fix:** use `<CSharpValue>` (read) or `<CSharpReference>` (write) child-element form for anything non-literal.

**Attribute form is safe for:** literal strings on `InArgument<String>`, enums, numbers, booleans, `TimeSpan` literals, `{x:Null}` — values with a direct type converter that bypasses the expression parser.

## `OutArgument<T>` attribute form fails at parse time

`<uix:NGetText TextString="statusText"/>` raises `Failed to create a 'TextString' from the text 'statusText'` — `TextString` is `OutArgument<String>`, not a plain property, so the XAML parser has no converter for it. Always use the `<OutArgument>` + `<CSharpReference>` child form for output bindings.

## `ThrowIfNotInTree` — variable declared outside the `ActivityAction` scope

`OutArgument<T>` + `<CSharpReference>` bound to a variable declared on a `Sequence` **outside** the `ActivityAction` body passes validation but throws at runtime:

```
System.InvalidOperationException: The argument of type 'System.String' cannot be used.
Make sure that it is declared on an activity.
  at System.Activities.Argument.ThrowIfNotInTree()
```

**Typical case:** a UI activity inside `<uix:NApplicationCard.Body><ActivityAction><Sequence>` writes an output to a variable declared on the *outer* `Sequence` rather than the inner one.

**Fix:** declare the variable on the `Sequence.Variables` immediately inside the `ActivityAction`, not on a parent `Sequence` outside it.
