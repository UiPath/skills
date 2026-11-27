# Verify Expression with Operator

Compares two expressions using a specified operator and asserts the comparison is true. Supports equality, inequality, relational comparisons, string containment, and regex matching. If the assertion fails, the test case is marked as failed.

**Class:** `UiPath.Testing.Activities.VerifyExpressionWithOperator`
**Assembly:** `UiPath.Testing.Activities`
**Category:** Testing > Verification

```xml
xmlns:uta="clr-namespace:UiPath.Testing.Activities;assembly=UiPath.Testing.Activities"
```

---

## Input

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `FirstExpression` | `InArgument<Object>` | Yes | The left-hand side of the comparison (the actual value). |
| `Operator` | `Comparison` | Yes | The operator used to compare the two expressions. See enum values below. |
| `SecondExpression` | `InArgument<Object>` | Yes | The right-hand side of the comparison (the expected value). |

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

## Enum: `Comparison`

| Value | Symbol | Description |
|-------|--------|-------------|
| `Equality` | `=` | Asserts `FirstExpression = SecondExpression`. |
| `Inequality` | `<>` | Asserts `FirstExpression <> SecondExpression`. |
| `GreaterThan` | `>` | Asserts `FirstExpression > SecondExpression`. |
| `GreaterThanOrEqual` | `>=` | Asserts `FirstExpression >= SecondExpression`. |
| `LessThan` | `<` | Asserts `FirstExpression < SecondExpression`. |
| `LessThanOrEqual` | `<=` | Asserts `FirstExpression <= SecondExpression`. |
| `Contains` | `Contains` | Asserts that `FirstExpression` contains `SecondExpression` (string containment). |
| `RegexMatch` | `Regex-Match` | Asserts that `FirstExpression` matches the regex pattern in `SecondExpression`. |

---

## Project Settings

| Property | Setting Key | Description |
|----------|-------------|-------------|
| `OutputMessageFormat` | `VerifyActivitiesOutputFormat` / `VerifyExpressionWithOperatorOutputFormat` | Default message format for all instances in the project. |

---

## XAML Example

```xml
<!-- Assert actual equals expected -->
<uta:VerifyExpressionWithOperator
  DisplayName="Verify Order Total"
  FirstExpression="[actualTotal]"
  Operator="Equality"
  SecondExpression="[expectedTotal]"
  TakeScreenshotInCaseOfFailingAssertion="True" />

<!-- Assert string contains substring -->
<uta:VerifyExpressionWithOperator
  DisplayName="Verify Error Message"
  FirstExpression="[errorMessage]"
  Operator="Contains"
  SecondExpression="&quot;Invalid input&quot;"
  TakeScreenshotInCaseOfFailingAssertion="True" />

<!-- Assert value matches regex -->
<uta:VerifyExpressionWithOperator
  DisplayName="Verify Email Format"
  FirstExpression="[email]"
  Operator="RegexMatch"
  SecondExpression="&quot;^[^@]+@[^@]+\.[^@]+$&quot;" />
```
