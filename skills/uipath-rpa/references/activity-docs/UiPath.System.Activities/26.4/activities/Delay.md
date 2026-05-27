# Delay

> **On the [Common Activity Card](../../../../common-activity-card.md)** — prefer the card for routine authoring.

`System.Activities.Statements.Delay`

Pauses workflow execution for a fixed duration.

**Package:** `System.Activities` (ships in .NET; referenced via `UiPath.System.Activities`)
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Duration` | Duration | `InArgument` | `TimeSpan` | Yes | — | How long to wait. Expression must produce a `TimeSpan`. |

## XAML Example

```xml
<Delay xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
       xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"
       xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
       DisplayName="Delay">
  <Delay.Duration>
    <InArgument x:TypeArguments="s:TimeSpan">
      <VisualBasicValue x:TypeArguments="s:TimeSpan" ExpressionText="TimeSpan.FromSeconds(5)" />
    </InArgument>
  </Delay.Duration>
</Delay>
```

## Notes

- `Duration` is mandatory; an unset `Duration` is a runtime error, not a `validate` error.
- Expression forms:
  - VB projects may use bracket shorthand: `Duration="[TimeSpan.FromSeconds(5)]"` or the property-element form above.
  - C# projects must use `<CSharpValue x:TypeArguments="s:TimeSpan">TimeSpan.FromSeconds(5)</CSharpValue>` inside the `InArgument`, or a literal attribute such as `Duration="00:00:05"` for fixed durations. Do not use bracket shorthand in C# XAML.
- `Delay` blocks the workflow's host thread for the full duration — use sparingly inside `ForEach` or `While` bodies where it multiplies latency.
- Do **not** use `Delay` as a substitute for waiting on an external condition. Prefer `RetryScope`, `WaitForElement`, or a polling loop with a `Condition` for state-dependent waits.
- `activities get-default-xaml` for `Delay` returns `<Delay />` only — `Duration` is invisible to the CLI.
- `Delay` is a leaf activity. It does not need a `<Sequence>` wrap around itself; its parent container slot still must be `<Sequence>`-wrapped per Rule 24.
