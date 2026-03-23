# Testing — Verification / Assertion APIs

All verification methods on the `testing` service (`ITestingService`). Each method returns `bool` — `true` if passed, `false` if failed. For general info see [testing.md](testing.md).

---

## VerifyExpression

Verifies a boolean expression.

### Overloads

```csharp
// Minimal — just the expression
bool VerifyExpression(bool expression);

// With output message
bool VerifyExpression(bool expression, string outputMessageFormat);

// Full parameters
bool VerifyExpression(
    bool expression,
    string outputMessageFormat,
    bool continueOnFailure,
    string alternativeVerificationTitle,
    bool takeScreenshotInCaseOfFailingAssertion,
    bool takeScreenshotInCaseOfSucceedingAssertion
);
```

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `expression` | `bool` | — | The boolean expression to verify |
| `outputMessageFormat` | `string` | `null` | Custom output message. Supports placeholders: `{LeftExpression}`, `{LeftExpressionText}`, `{RightExpression}`, `{RightExpressionText}`, `{Result}`, `{Operator}` |
| `continueOnFailure` | `bool` | `false` | If `true`, execution continues even if the verification fails |
| `alternativeVerificationTitle` | `string` | `null` | Title displayed in Orchestrator. If not set, defaults to the activity's DisplayName |
| `takeScreenshotInCaseOfFailingAssertion` | `bool` | `false` | Take screenshot on failure |
| `takeScreenshotInCaseOfSucceedingAssertion` | `bool` | `false` | Take screenshot on success |

### Usage

```csharp
testing.VerifyExpression(count > 0, "Count should be positive");

testing.VerifyExpression(
    name.Contains("test"),
    "Name should contain 'test'",
    continueOnFailure: true,
    alternativeVerificationTitle: "Name validation",
    takeScreenshotInCaseOfFailingAssertion: true,
    takeScreenshotInCaseOfSucceedingAssertion: false
);
```

---

## VerifyExpressionWithOperator

Verifies two expressions using a comparison operator.

### Overloads

```csharp
// Minimal
bool VerifyExpressionWithOperator(
    object firstExpression,
    Comparison operatorValue,
    object secondExpression,
    string outputMessageFormat = null
);

// Full parameters
bool VerifyExpressionWithOperator(
    object firstExpression,
    Comparison operatorValue,
    object secondExpression,
    string outputMessageFormat,
    bool continueOnFailure,
    string alternativeVerificationTitle,
    bool takeScreenshotInCaseOfFailingAssertion,
    bool takeScreenshotInCaseOfSucceedingAssertion
);
```

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `firstExpression` | `object` | — | The left-hand expression |
| `operatorValue` | `Comparison` | — | The comparison operator |
| `secondExpression` | `object` | — | The right-hand expression |
| `outputMessageFormat` | `string` | `null` | Custom output message with placeholders |
| `continueOnFailure` | `bool` | `false` | Continue execution on failure |
| `alternativeVerificationTitle` | `string` | `null` | Title displayed in Orchestrator |
| `takeScreenshotInCaseOfFailingAssertion` | `bool` | `false` | Take screenshot on failure |
| `takeScreenshotInCaseOfSucceedingAssertion` | `bool` | `false` | Take screenshot on success |

### `Comparison` enum values

| Value | Operator | Description |
|---|---|---|
| `Comparison.Equality` | `=` | Equal |
| `Comparison.Inequality` | `<>` | Not equal |
| `Comparison.GreaterThan` | `>` | Greater than |
| `Comparison.GreaterThanOrEqual` | `>=` | Greater than or equal |
| `Comparison.LessThan` | `<` | Less than |
| `Comparison.LessThanOrEqual` | `<=` | Less than or equal |
| `Comparison.Contains` | `Contains` | First contains second |
| `Comparison.RegexMatch` | `Regex-Match` | First matches regex in second |

### Usage

```csharp
testing.VerifyExpressionWithOperator(actualCount, Comparison.Equality, expectedCount, "Counts should match");
testing.VerifyExpressionWithOperator(price, Comparison.GreaterThan, 0, "Price must be positive");
```

---

## Convenience Verification Methods

These are shorthand methods that internally call `VerifyExpressionWithOperator` with a specific `Comparison` operator.

### VerifyAreEqual

Verifies two expressions are equal (`Comparison.Equality`).

```csharp
bool VerifyAreEqual(object firstExpression, object secondExpression, string outputMessageFormat = null);
```

```csharp
testing.VerifyAreEqual("Completed", status, "Status should be Completed");
testing.VerifyAreEqual(expectedCount, actualCount, "Counts should match");
```

### VerifyAreNotEqual

Verifies two expressions are not equal (`Comparison.Inequality`).

```csharp
bool VerifyAreNotEqual(object firstExpression, object secondExpression, string outputMessageFormat = null);
```

```csharp
testing.VerifyAreNotEqual("Pending", status, "Status should have changed from Pending");
```

### VerifyIsGreater

Verifies the first expression is greater than the second (`Comparison.GreaterThan`).

```csharp
bool VerifyIsGreater(object firstExpression, object secondExpression, string outputMessageFormat = null);
```

```csharp
testing.VerifyIsGreater(revenue, 1000, "Revenue should exceed 1000");
```

### VerifyIsGreaterOrEqual

Verifies the first expression is greater than or equal to the second (`Comparison.GreaterThanOrEqual`).

```csharp
bool VerifyIsGreaterOrEqual(object firstExpression, object secondExpression, string outputMessageFormat = null);
```

```csharp
testing.VerifyIsGreaterOrEqual(itemCount, minimumRequired, "Should meet minimum item count");
```

### VerifyIsLess

Verifies the first expression is less than the second (`Comparison.LessThan`).

```csharp
bool VerifyIsLess(object firstExpression, object secondExpression, string outputMessageFormat = null);
```

```csharp
testing.VerifyIsLess(responseTime, 5000, "Response time should be under 5 seconds");
```

### VerifyIsLessOrEqual

Verifies the first expression is less than or equal to the second (`Comparison.LessThanOrEqual`).

```csharp
bool VerifyIsLessOrEqual(object firstExpression, object secondExpression, string outputMessageFormat = null);
```

```csharp
testing.VerifyIsLessOrEqual(errorCount, maxAllowedErrors, "Errors should not exceed maximum");
```

### VerifyContains

Verifies the first expression contains the second (`Comparison.Contains`).

```csharp
bool VerifyContains(object firstExpression, object secondExpression, string outputMessageFormat = null);
```

```csharp
testing.VerifyContains(fullMessage, "success", "Message should contain 'success'");
```

### VerifyIsRegexMatch

Verifies the first expression matches the regex pattern in the second (`Comparison.RegexMatch`).

```csharp
bool VerifyIsRegexMatch(object firstExpression, object secondExpression, string outputMessageFormat = null);
```

```csharp
testing.VerifyIsRegexMatch(email, @"^[\w.-]+@[\w.-]+\.\w+$", "Should be a valid email format");
```

---

## VerifyRange

Verifies a value is within (or outside) a specified range.

### Overloads

```csharp
// Minimal
bool VerifyRange(
    object expression,
    VerificationType verificationType,
    object lowerLimit,
    object upperLimit,
    string outputMessageFormat = null
);

// Full parameters
bool VerifyRange(
    object expression,
    VerificationType verificationType,
    object lowerLimit,
    object upperLimit,
    string outputMessageFormat,
    bool continueOnFailure,
    string alternativeVerificationTitle,
    bool takeScreenshotInCaseOfFailingAssertion,
    bool takeScreenshotInCaseOfSucceedingAssertion
);
```

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `expression` | `object` | — | The value to verify |
| `verificationType` | `VerificationType` | — | `IsWithin` or `IsNotWithin` the range |
| `lowerLimit` | `object` | — | The lower bound of the range |
| `upperLimit` | `object` | — | The upper bound of the range |
| `outputMessageFormat` | `string` | `null` | Custom output message |
| `continueOnFailure` | `bool` | `false` | Continue execution on failure |
| `alternativeVerificationTitle` | `string` | `null` | Title displayed in Orchestrator |
| `takeScreenshotInCaseOfFailingAssertion` | `bool` | `false` | Take screenshot on failure |
| `takeScreenshotInCaseOfSucceedingAssertion` | `bool` | `false` | Take screenshot on success |

### `VerificationType` enum

| Value | Description |
|---|---|
| `VerificationType.IsWithin` | Value must be inside the range |
| `VerificationType.IsNotWithin` | Value must be outside the range |

### Usage

```csharp
// Value should be within range
testing.VerifyRange(processingTime, VerificationType.IsWithin, 0.5, 5.0, "Processing time should be 0.5-5s");

// Value should be outside range
testing.VerifyRange(errorRate, VerificationType.IsNotWithin, 10, 100, "Error rate should not be 10-100%");
```
