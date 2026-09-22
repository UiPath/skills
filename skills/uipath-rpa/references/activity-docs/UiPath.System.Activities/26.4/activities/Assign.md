# Assign

> **On the [Common Activity Card](../../../../common-activity-card.md)** — prefer the card for routine authoring.

`System.Activities.Statements.Assign`

Assigns the value of an expression to a variable or argument. The activity element carries no type arguments; the types live on its `OutArgument` and `InArgument` children.

**Package:** `System.Activities` (ships in .NET; referenced via `UiPath.System.Activities`)
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Value` | Value | `InArgument<T>` | `T`, the target's type | Yes | — | The expression whose result is assigned to `To`. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `To` | To | `OutArgument<T>` | `T`, the target's type | The target variable or argument that receives the value. Must be a writable expression — typically a variable reference. |

## XAML Example

```xml
<Assign DisplayName="Set Counter">
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

Type both arguments with the target's type; use `x:Object` only when the target itself is untyped.

## Notes

- The typed `OutArgument`/`InArgument` children give the validator a typed expression and surface type-mismatch errors at `validate` time.
- The `To` expression must be a writable reference (a variable, an argument, or an indexer). It is **not** an assignment statement embedded in the expression text — Studio's emitter uses `VisualBasicReference` (or `CSharpReference` in C# projects) for the writable side and `VisualBasicValue` (or `CSharpValue`) for the readable side.
- For chained assignments, emit one `Assign` per target. Studio does not support multi-target `Assign`.
- `activities get-default-xaml` for `Assign` returns `<Assign />` only — both arguments are invisible to the CLI.
