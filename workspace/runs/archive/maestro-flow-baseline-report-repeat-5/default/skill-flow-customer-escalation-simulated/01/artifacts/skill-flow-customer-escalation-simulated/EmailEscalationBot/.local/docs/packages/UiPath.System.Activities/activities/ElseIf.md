# Else If

`UiPath.Core.Activities.IfElseIfV2`

Else If activity chooses between different paths based on a series of conditions being true or false.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Condition` | Condition | `InArgument` | `bool` | No | — | The Boolean condition for the leading `If` branch. Additional Else If branches each have their own condition. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ElseIfs` | Else Ifs | `BindingList<IfElseIfBlock>` | — | The ordered list of Else If branch blocks, each with its own condition and body. |
| `Else` | "Else" | `Activity` | — | The body executed when no branch condition is satisfied. Optional. |

## XAML Example

```xml
<ui:IfElseIfV2
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Else If">
  <ui:IfElseIfV2.Condition>
    <InArgument x:TypeArguments="x:Boolean">
      <VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="score &gt;= 90" />
    </InArgument>
  </ui:IfElseIfV2.Condition>
  <!-- Then body -->
  <ui:IfElseIfV2.ElseIfs>
    <ui:IfElseIfBlock>
      <ui:IfElseIfBlock.Condition>
        <InArgument x:TypeArguments="x:Boolean">
          <VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="score &gt;= 70" />
        </InArgument>
      </ui:IfElseIfBlock.Condition>
      <!-- Else If body -->
    </ui:IfElseIfBlock>
  </ui:IfElseIfV2.ElseIfs>
  <ui:IfElseIfV2.Else>
    <Sequence DisplayName="Else">
      <!-- fallback activities -->
    </Sequence>
  </ui:IfElseIfV2.Else>
</ui:IfElseIfV2>
```

## Notes

- **Else If** is a container/scope activity with multiple branches: an initial `If` branch, zero or more `Else If` branches, and an optional `Else` branch.
- Branches are evaluated in order; the first branch whose condition is `True` is executed and the remaining branches are skipped.
- The `AddElseIfButton` property (widget `AddActivityWidget`) is a designer-only control for appending new Else If branches — it is not a runtime argument.
- The `Then` body (the first `If` branch container) has `isVisible: false` in the JSON metadata; it is managed directly by the designer canvas rather than the properties panel.
- `BlockType` (`IfElseIfBlockType`) is a hidden internal design-time property that controls the block kind; it is not intended for direct configuration.
