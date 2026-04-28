# Verify Expression

Evaluates a Boolean expression and asserts that it is `true`. If the expression evaluates to `false`, the test case is marked as failed. Optionally captures screenshots on pass or fail and writes a formatted result message to the test report.

**Class:** `UiPath.Testing.Activities.VerifyExpression`
**Assembly:** `UiPath.Testing.Activities`
**Category:** Testing > Verification

```xml
xmlns:uta="clr-namespace:UiPath.Testing.Activities;assembly=UiPath.Testing.Activities"
```

---

## Input

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `Expression` | `InArgument<Boolean>` | Yes | The Boolean expression to verify. The assertion passes when this evaluates to `true`. |

## Messages

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `OutputMessageFormat` | `InArgument<String>` | No | *(project setting)* | Custom format string for the result message written to the test report. Supported placeholders: `{Expression}`, `{Result}`. Example: `"{Expression} has result {Result}"`. |

## Common

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `TakeScreenshotInCaseOfFailingAssertion` | `InArgument<Boolean>` | No | `false` | If `true`, takes a screenshot when the assertion fails. |
| `TakeScreenshotInCaseOfSucceedingAssertion` | `InArgument<Boolean>` | No | `false` | If `true`, takes a screenshot when the assertion passes. |

---

## Project Settings

The `OutputMessageFormat` default is configurable in UiPath Studio under **Project Settings**:

| Property | Setting Key | Description |
|----------|-------------|-------------|
| `OutputMessageFormat` | `VerifyActivitiesOutputFormat` / `VerifyExpressionOutputFormat` | Default message format for all Verify Expression instances in the project. |

---

## XAML Example

```xml
<!-- Basic assertion -->
<uta:VerifyExpression
  DisplayName="Verify Expression"
  Expression="[actualValue = expectedValue]"
  TakeScreenshotInCaseOfFailingAssertion="True" />

<!-- With custom message format -->
<uta:VerifyExpression
  DisplayName="Verify Login Succeeded"
  Expression="[isLoggedIn]"
  OutputMessageFormat="&quot;Login check: {Expression} → {Result}&quot;"
  TakeScreenshotInCaseOfFailingAssertion="True" />
```
