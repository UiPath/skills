# Throw

> **On the [Common Activity Card](../../../../common-activity-card.md)** — prefer the card for routine authoring.

`System.Activities.Statements.Throw`

Throws a new exception. Used to signal a business rule violation or an unrecoverable state.

**Package:** `System.Activities` (ships in .NET; referenced via `UiPath.System.Activities`)
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Exception` | Exception | `InArgument` | `System.Exception` | Yes | — | The exception instance to throw. Expression must construct an exception (typically via a `new <ExceptionType>(...)` expression). |

## XAML Example

```xml
<Throw xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
       xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"
       DisplayName="Throw">
  <Throw.Exception>
    <InArgument x:TypeArguments="s:Exception">
      <VisualBasicValue x:TypeArguments="s:Exception" ExpressionText="new InvalidOperationException(&quot;Invoice total is negative&quot;)" />
    </InArgument>
  </Throw.Exception>
</Throw>
```

## Notes

- `Exception` is a constructor expression, not a string. `Throw.Exception = "message"` is invalid — the expression must evaluate to an `Exception` instance: `new BusinessRuleException("…")`, `new InvalidOperationException("…")`, etc.
- Use `Throw` when you want a fresh exception with a new stack trace; use `Rethrow` (only valid inside a `Catch` body) to re-raise the currently-caught exception with its original stack trace preserved.
- For business-rule violations, prefer a domain-specific exception type (e.g., `UiPath.Core.Activities.BusinessRuleException`) over `Exception` directly — it gives downstream `Catch` handlers a way to distinguish business errors from system errors.
- `activities get-default-xaml` for `Throw` returns `<Throw />` only — the `Exception` argument is invisible to the CLI.
- `Throw` is a leaf activity. Its parent container slot must be `<Sequence>`-wrapped per Rule 24.
