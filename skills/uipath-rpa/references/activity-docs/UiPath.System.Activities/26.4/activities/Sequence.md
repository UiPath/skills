# Sequence

> **On the [Common Activity Card](../../../../common-activity-card.md)** — prefer the card for routine authoring.

`System.Activities.Statements.Sequence`

Executes a set of contained activities in sequential order. Sequence is the canonical container for ordered execution and acts as the body wrap for every container slot in other activities (see Rule 24).

**Package:** `System.Activities` (ships in .NET; referenced via `UiPath.System.Activities`)
**Category:** Workflow

## Properties

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Activities` | Activities | `Collection<Activity>` | — | The ordered list of child activities. Set by nesting child elements directly inside `<Sequence>`. |
| `Variables` | Variables | `Collection<Variable>` | — | Variables scoped to this Sequence. Set via the nested `<Sequence.Variables>` element. |

`Sequence` exposes no input or output arguments.

## XAML Example

```xml
<Sequence xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
          xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
          DisplayName="Sequence">
  <Sequence.Variables>
    <Variable x:TypeArguments="x:String" Name="message" />
    <Variable x:TypeArguments="x:Int32" Name="counter" />
  </Sequence.Variables>
  <!-- child activities go here, in execution order -->
</Sequence>
```

## Notes

- `Sequence` is the **container wrap** required by Rule 24 inside every body/branch slot of `If`, `Switch`, `TryCatch`, `While`, `DoWhile`, `ForEach`, `Pick`, etc. — even when only one child activity is present.
- `Variables` declared on a `Sequence` are visible to every descendant activity within it and go out of scope when the `Sequence` ends. Prefer the smallest enclosing `Sequence` for variable declarations.
- `activities get-default-xaml` for `Sequence` returns `<Sequence />` only — the namespace and `Variables` shape are invisible to the CLI and must come from this doc.
- ViewState is **optional** for Sequences (Rule 20). Required only when the parent is a `Flowchart`, `StateMachine`, or `ProcessDiagram`.
