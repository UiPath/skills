# Assign

> **On the [Common Activity Card](../../../../common-activity-card.md)** — prefer the card for routine authoring.

`System.Activities.Statements.Assign` (non-generic) / `System.Activities.Statements.Assign`1` (generic)

Assigns the value of an expression to a variable or argument. Studio emits the generic `Assign<T>` form when the target variable has a declared type; the non-generic form is used only when both sides are `Object`.

**Package:** `System.Activities` (ships in .NET; referenced via `UiPath.System.Activities`)
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Value` | Value | `InArgument<T>` | `T` (or `object` for the non-generic form) | Yes | — | The expression whose result is assigned to `To`. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `To` | To | `OutArgument<T>` | `T` (or `object` for the non-generic form) | The target variable or argument that receives the value. Must be a writable expression — typically a variable reference. |

## XAML Example — generic `Assign<T>` (preferred)

```xml
<Assign x:TypeArguments="x:Int32"
        xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        DisplayName="Assign">
  <Assign.To>
    <OutArgument x:TypeArguments="x:Int32">
      <VisualBasicReference x:TypeArguments="x:Int32" ExpressionText="counter" />
    </OutArgument>
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="x:Int32">
      <VisualBasicValue x:TypeArguments="x:Int32" ExpressionText="counter + 1" />
    </InArgument>
  </Assign.Value>
</Assign>
```

## XAML Example — non-generic `Assign`

```xml
<Assign xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
        DisplayName="Assign">
  <Assign.To>
    <OutArgument x:TypeArguments="x:Object" />
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="x:Object" />
  </Assign.Value>
</Assign>
```

## Notes

- Prefer the **generic `Assign<T>`** form whenever the target variable has a known type — it gives the validator a typed expression and surfaces type-mismatch errors at `validate` time instead of at runtime.
- The `To` expression must be a writable reference (a variable, an argument, or an indexer). It is **not** an assignment statement embedded in the expression text — Studio's emitter uses `VisualBasicReference` (or `CSharpReference` in C# projects) for the writable side and `VisualBasicValue` (or `CSharpValue`) for the readable side.
- For chained assignments, emit one `Assign` per target. Studio does not support multi-target `Assign`.
- `activities get-default-xaml` for `Assign` returns `<Assign />` only — both arguments are invisible to the CLI.
