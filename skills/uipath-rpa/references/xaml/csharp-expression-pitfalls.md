# C# Expression Pitfalls

**Scope:** XAML workflow files in projects whose `project.json` has `expressionLanguage: CSharp`. These rules govern how XAML expressions are authored — they do **not** apply to VB XAML projects, and they do **not** apply to coded workflows (`.cs` files with `[Workflow]` / `[TestCase]`). Coded workflows are plain C# — none of the `CSharpValue` / `CSharpReference` / attribute-form rules below are relevant there.

Failure modes in scope: all pass static `validate` validation — they only surface at `CacheMetadata` time under `uip rpa build` or `uip rpa run`.

For the canonical binding form per property, see [csharp-activity-binding-guide.md](csharp-activity-binding-guide.md).

## Attribute-form expressions fail at runtime

Any non-literal attribute value on an `InArgument<T>` / `OutArgument<T>` property (e.g. `Message="logMessage"`, `TextString="statusText"`) is deserialized as `VisualBasicValue<T>` by the XAML attribute parser — regardless of the project's `expressionLanguage`. On non-Legacy projects the VB JIT is disabled, so these fail at runtime:

```
System.InvalidOperationException: JIT compilation is disabled for non-Legacy projects.
ExpressionToCompile { Code = "logMessage" ... } should have been compiled by the Studio Compiler.
```

**Fix:** use `<CSharpValue>` (read) or `<CSharpReference>` (write) child-element form for anything non-literal.

**Attribute form is safe for:** literal strings on `InArgument<String>`, enums, numbers, booleans, `TimeSpan` literals, `{x:Null}` — values with a direct type converter that bypasses the expression parser.

## `OutArgument<T>` attribute form fails at parse time

`<uix:NGetText TextString="statusText"/>` raises `Failed to create a 'TextString' from the text 'statusText'` — `TextString` is `OutArgument<String>`, not a plain property, so the XAML parser has no converter for it. Always use the `<OutArgument>` + `<CSharpReference>` child form for output bindings.

## `ThrowIfNotInTree` at runtime — two causes

Same runtime stack, two distinct root causes:

```
System.InvalidOperationException: The argument of type 'System.String' cannot be used.
Make sure that it is declared on an activity.
  at System.Activities.Argument.ThrowIfNotInTree()
```

**Cause 1 — variable declared outside the `ActivityAction` scope.** `OutArgument<T>` + `<CSharpReference>` bound to a variable declared on a `Sequence` **outside** the `ActivityAction` body passes validation but throws at runtime.

- **Typical case:** a UI activity inside `<uix:NApplicationCard.Body><ActivityAction><Sequence>` writes an output to a variable declared on the *outer* `Sequence` rather than the inner one.
- **Fix:** declare the variable on the `Sequence.Variables` immediately inside the `ActivityAction`, not on a parent `Sequence` outside it.

**Cause 2 — UIA activity authored without its `Version` attribute.** A UIA activity missing the `Version` its `activities get-default-xaml` starter emits (e.g. `NGetText` without `Version="V5"`) throws `ThrowIfNotInTree` at runtime on its argument bindings even when variable scoping is correct. This passes BOTH `validate` AND `build` clean — it surfaces only at run.

- **Diagnosis rule:** when scoping is verified correct, diff the authored activity against its `uip rpa activities get-default-xaml` starter and restore any missing attributes — the starter's `Version` in particular. Never strip an attribute the starter emits.
