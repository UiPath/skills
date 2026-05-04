# Verify Range

Verifies that a value falls within (or outside) a specified range defined by a lower and upper limit. If the assertion fails, the test case is marked as failed.

**Class:** `UiPath.Testing.Activities.VerifyRange`
**Assembly:** `UiPath.Testing.Activities`
**Category:** Testing > Verification

```xml
xmlns:uta="clr-namespace:UiPath.Testing.Activities;assembly=UiPath.Testing.Activities"
```

---

## Input

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `Expression` | `InArgument<Object>` | Yes | The value to verify against the range. |
| `LowerLimit` | `InArgument<Object>` | Yes | The lower bound of the range (inclusive). |
| `UpperLimit` | `InArgument<Object>` | Yes | The upper bound of the range (inclusive). |
| `VerificationType` | `VerificationType` | Yes | Whether to assert the value is `IsWithin` or `IsNotWithin` the range. |

## Messages

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `OutputMessageFormat` | `InArgument<String>` | No | *(project setting)* | Custom format string for the result message. Supported placeholders: `{LeftExpression}`, `{LeftExpressionText}`, `{RightExpression}`, `{RightExpressionText}`, `{Result}`, `{Operator}`. |

## Common

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `TakeScreenshotInCaseOfFailingAssertion` | `InArgument<Boolean>` | No | `false` | If `true`, takes a screenshot when the assertion fails. |
| `TakeScreenshotInCaseOfSucceedingAssertion` | `InArgument<Boolean>` | No | `false` | If `true`, takes a screenshot when the assertion passes. |

---

## Enum: `VerificationType`

| Value | Description |
|-------|-------------|
| `IsWithin` | Asserts the expression is within `[LowerLimit, UpperLimit]` (inclusive on both ends). |
| `IsNotWithin` | Asserts the expression is outside the range. |

---

## Project Settings

| Property | Setting Key | Description |
|----------|-------------|-------------|
| `OutputMessageFormat` | `VerifyActivitiesOutputFormat` / `VerifyRangeOutputFormat` | Default message format for all Verify Range instances in the project. |

---

## XAML Example

```xml
<!-- Assert value is within range [1, 100] -->
<uta:VerifyRange
  DisplayName="Verify Score In Range"
  Expression="[score]"
  LowerLimit="[1]"
  UpperLimit="[100]"
  VerificationType="IsWithin"
  TakeScreenshotInCaseOfFailingAssertion="True" />

<!-- Assert value is outside range (not within [-10, 0]) -->
<uta:VerifyRange
  DisplayName="Verify Positive Balance"
  Expression="[balance]"
  LowerLimit="[-10]"
  UpperLimit="[0]"
  VerificationType="IsNotWithin" />
```
