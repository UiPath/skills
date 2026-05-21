# Switch

> **On the [Common Activity Card](../../../../common-activity-card.md)** — prefer the card for routine authoring.

`System.Activities.Statements.Switch`1`

Evaluates an expression and executes the case whose key matches, or the default branch when no key matches. Generic over the expression type `T`.

**Package:** `System.Activities` (ships in .NET; referenced via `UiPath.System.Activities`)
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Expression` | Expression | `InArgument<T>` | `T` | Yes | — | The value compared against the case keys. The generic type `T` is set on the activity via `x:TypeArguments`. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Cases` | Cases | `IDictionary<T, Activity>` | empty | Dictionary of case branches keyed by literal values of type `T`. Each case body is a child element with an `x:Key` attribute carrying the literal. |
| `Default` | Default | `Activity` | — | Branch executed when `Expression` matches no case key. Set via the nested `<Switch.Default>` element. |

## XAML Example

```xml
<Switch x:TypeArguments="x:Int32"
        xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        DisplayName="Switch">
  <Switch.Expression>
    <InArgument x:TypeArguments="x:Int32">
      <VisualBasicValue x:TypeArguments="x:Int32" ExpressionText="status" />
    </InArgument>
  </Switch.Expression>
  <Sequence x:Key="1" DisplayName="Case 1">
    <!-- case body for status == 1 -->
  </Sequence>
  <Sequence x:Key="2" DisplayName="Case 2">
    <!-- case body for status == 2 -->
  </Sequence>
  <Switch.Default>
    <Sequence DisplayName="Default">
      <!-- fallback body -->
    </Sequence>
  </Switch.Default>
</Switch>
```

## Notes

- Each case body and the `Switch.Default` body **must wrap their content in `<Sequence>`** per Rule 24.
- Case keys are declared via `x:Key="<literal>"` on each case-body child element directly inside `<Switch>`. The `Cases` dictionary is not declared explicitly — child elements with `x:Key` populate it.
- `x:TypeArguments` on the `<Switch>` element fixes `T`. For string keys use `x:TypeArguments="x:String"` and set `x:Key="someString"`; for integers use `x:TypeArguments="x:Int32"`.
- `activities get-default-xaml` for `Switch`1` returns `<Switch x:TypeArguments="x:Object" />` only — `Expression`, every case, and `Default` are invisible to the CLI.
- A `Switch` with no cases and no `Default` is legal but does nothing.
