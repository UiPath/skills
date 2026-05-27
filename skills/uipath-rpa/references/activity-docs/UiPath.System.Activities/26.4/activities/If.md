# If

> **On the [Common Activity Card](../../../../common-activity-card.md)** — prefer the card for routine authoring.

`System.Activities.Statements.If`

Executes one of two contained activities depending on the value of a Boolean condition.

**Package:** `System.Activities` (ships in .NET; referenced via `UiPath.System.Activities`)
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Condition` | Condition | `InArgument` | `bool` | Yes | — | The Boolean expression evaluated once. `True` runs `Then`; `False` runs `Else`. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Then` | Then | `Activity` | — | Branch executed when `Condition` is `True`. Set via the nested `<If.Then>` element. |
| `Else` | Else | `Activity` | — | Branch executed when `Condition` is `False`. Set via the nested `<If.Else>` element. Omit entirely when there is no else branch. |

## XAML Example

```xml
<If xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    DisplayName="If">
  <If.Condition>
    <InArgument x:TypeArguments="x:Boolean">
      <VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="counter &lt; 10" />
    </InArgument>
  </If.Condition>
  <If.Then>
    <Sequence DisplayName="Then">
      <!-- then branch -->
    </Sequence>
  </If.Then>
  <If.Else>
    <Sequence DisplayName="Else">
      <!-- else branch -->
    </Sequence>
  </If.Else>
</If>
```

## Notes

- Both `If.Then` and `If.Else` slots **must wrap their body in `<Sequence>`** per Rule 24, even when the branch contains only one activity.
- Omit `<If.Else>` entirely when the workflow has no else branch. Do not emit an empty `<If.Else></If.Else>` — it has no effect and clutters the workflow.
- `activities get-default-xaml` for `If` returns `<If />` only — every property and both branch slots are invisible to the CLI; this doc is the only authoritative source for the shape.
- For multi-branch decisions (`else if … else if … else`), use `UiPath.Core.Activities.IfElseIfV2` (see `ElseIf.md`) instead of nesting `If` inside `If.Else`.
