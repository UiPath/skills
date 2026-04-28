# Create Comparison Rule

Creates a `ComparisonRule` object that can be passed to **Compare Text** or **Compare PDF Documents** to exclude dynamic sections of text from comparison. Rules match patterns using either wildcard or regex syntax, replacing matched portions with a placeholder in the diff output.

**Class:** `UiPath.Testing.Activities.CreateComparisonRule`
**Assembly:** `UiPath.Testing.Activities`
**Category:** Testing > Verification

```xml
xmlns:uta="clr-namespace:UiPath.Testing.Activities;assembly=UiPath.Testing.Activities"
```

---

## Input

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `RuleName` | `InArgument<String>` | No | — | A name for the rule. Used as the placeholder text in diff output when `UsePlaceholder` is `true`. |
| `ComparisonRuleType` | `ComparisonRuleType` | No | `RegexRule` | The matching technique: `RegexRule` or `WildcardRule`. See enum below. |
| `Pattern` | `InArgument<String>` | No | — | The pattern to match in the text. Use regex syntax for `RegexRule`, glob-style wildcards (`*`, `?`) for `WildcardRule`. |
| `UsePlaceholder` | `InArgument<Boolean>` | No | `true` | If `true`, matched text in the diff is replaced by `[RuleName]`. If `false`, matched text is simply omitted. |

## Output

| Property | Type | Description |
|----------|------|-------------|
| `ComparisonRule` | `OutArgument<ComparisonRule>` | The created comparison rule object. Pass this to the `Rules` or `RulesList` property of **Compare Text** or **Compare PDF Documents**. |

## Common

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `ContinueOnError` | `InArgument<Boolean>` | No | `false` | If `true`, execution continues when the activity throws an error. |

---

## Enum: `ComparisonRuleType`

| Value | Description |
|-------|-------------|
| `RegexRule` | Pattern is a regular expression. Matches any text that satisfies the regex. |
| `WildcardRule` | Pattern uses glob-style wildcards (`*` matches any sequence of characters, `?` matches a single character). |

---

## Notes

- Create rules before calling **Compare Text** or **Compare PDF Documents**.
- Multiple rules can be collected into a list and passed to those activities' `RulesList` property.
- Typical use cases: excluding dates, timestamps, IDs, and other dynamic content from document comparisons.

---

## XAML Example

```xml
<!-- Rule to ignore date patterns like "01/15/2024" -->
<uta:CreateComparisonRule
  DisplayName="Create Date Rule"
  RuleName="&quot;DatePattern&quot;"
  ComparisonRuleType="RegexRule"
  Pattern="&quot;\d{2}/\d{2}/\d{4}&quot;"
  UsePlaceholder="True"
  ComparisonRule="[dateRule]"
  ContinueOnError="False" />

<!-- Rule to ignore any order ID starting with "ORD-" -->
<uta:CreateComparisonRule
  DisplayName="Create Order ID Rule"
  RuleName="&quot;OrderID&quot;"
  ComparisonRuleType="WildcardRule"
  Pattern="&quot;ORD-*&quot;"
  UsePlaceholder="True"
  ComparisonRule="[orderIdRule]" />
```

Then pass rules to **Compare Text**:
```xml
<uta:CompareText
  ...
  RulesList="[New List(Of ComparisonRule) From {dateRule, orderIdRule}]" />
```
