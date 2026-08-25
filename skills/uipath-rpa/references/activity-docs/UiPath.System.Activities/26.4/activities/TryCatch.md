# Try Catch

> **On the [Common Activity Card](../../../../common-activity-card.md)** — prefer the card for routine authoring.

`System.Activities.Statements.TryCatch`

Executes the `Try` body; when a child activity throws an exception, dispatches to the first `Catch` whose exception type matches. The `Finally` body runs after `Try` (and any matching `Catch`) regardless of outcome.

**Package:** `System.Activities` (ships in .NET; referenced via `UiPath.System.Activities`)
**Category:** Workflow

## Properties

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Try` | Try | `Activity` | — | The guarded body. Set via the nested `<TryCatch.Try>` element. |
| `Catches` | Catches | `Collection<Catch>` | empty | Ordered list of typed exception handlers. Set via the nested `<TryCatch.Catches>` element containing one `<Catch x:TypeArguments="...">` per handler. |
| `Finally` | Finally | `Activity` | — | Block executed after `Try` and any matching `Catch`. Set via the nested `<TryCatch.Finally>` element. Omit when not needed. |

Each `Catch<TException>` exposes:

| Name | Type | Description |
|------|------|-------------|
| `Action` | `ActivityAction<TException>` | The handler body. The caught exception is bound to a `DelegateInArgument<TException>` (typically named `exception`). |

## XAML Example

```xml
<TryCatch xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
          xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
          xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"
          DisplayName="Try Catch">
  <TryCatch.Try>
    <Sequence DisplayName="Try">
      <!-- guarded body -->
    </Sequence>
  </TryCatch.Try>
  <TryCatch.Catches>
    <Catch x:TypeArguments="s:Exception">
      <ActivityAction x:TypeArguments="s:Exception">
        <ActivityAction.Argument>
          <DelegateInArgument x:TypeArguments="s:Exception" Name="exception" />
        </ActivityAction.Argument>
        <Sequence DisplayName="Catch">
          <!-- handler body; reference the iterator variable "exception" -->
        </Sequence>
      </ActivityAction>
    </Catch>
  </TryCatch.Catches>
  <TryCatch.Finally>
    <Sequence DisplayName="Finally">
      <!-- finally body -->
    </Sequence>
  </TryCatch.Finally>
</TryCatch>
```

## Notes

- `Try`, every `Catch.Action`, and `Finally` **must wrap their body in `<Sequence>`** per Rule 24.
- Each `Catch` requires its own `<ActivityAction x:TypeArguments="...">` element holding a `<DelegateInArgument x:TypeArguments="..." Name="exception" />` and the handler `<Sequence>`. The `Name` of the `DelegateInArgument` is the variable name that the handler body uses to reference the caught exception.
- Order matters: the first `Catch` whose type the thrown exception is assignable to wins. Place more specific exception types before `s:Exception`.
- Use `Rethrow` inside a `Catch.Action` body to re-raise the current exception with its original stack trace; use `Throw` to raise a different exception.
- `activities get-default-xaml` for `TryCatch` returns `<TryCatch />` only — every slot is invisible to the CLI.
- Omit `<TryCatch.Finally>` entirely when no finally body is needed; do not emit an empty one.
