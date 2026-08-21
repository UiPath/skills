# Evaluate Business Rule

`UiPath.Core.Activities.EvaluateBusinessRule`

Evaluates a DMN (Decision Model and Notation) business rule file and returns the result.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `BusinessRule` | Business Rule | `InArgument` | `string` | Yes | — | The path or identifier of the DMN business rule file to evaluate. Supports expression auto-complete. |
| `Arguments` | Arguments | `Property` | `Dictionary<string, Argument>` | No | `new Dictionary<string, Argument>()` | The named input and output arguments passed to and from the business rule. Populated from the rule file definition. |
| `ArgumentsVariable` | Arguments variable | `Property` | `InArgument<Dictionary<string, object>>` | No | — | An alternative way to supply input arguments as a single dictionary variable instead of individual named arguments. |

## XAML Example

```xml
<ui:EvaluateBusinessRule
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Evaluate Business Rule">
  <ui:EvaluateBusinessRule.BusinessRule>
    <InArgument x:TypeArguments="x:String">
      <VisualBasicValue x:TypeArguments="x:String" ExpressionText="&quot;Rules\LoanApproval.dmn&quot;" />
    </InArgument>
  </ui:EvaluateBusinessRule.BusinessRule>
  <ui:EvaluateBusinessRule.Arguments>
    <!-- argument entries are populated automatically from the .dmn file -->
  </ui:EvaluateBusinessRule.Arguments>
</ui:EvaluateBusinessRule>
```

## Notes

- This activity is marked **experimental** in the designer (indicated by the `ExperimentalLabel` property rendered as an info label).
- `Arguments` and `ArgumentsVariable` provide two different ways to supply input data to the rule:
  - `Arguments` is a structured dictionary of typed `Argument` objects (input and output) that is populated automatically when a valid `BusinessRule` file is selected.
  - `ArgumentsVariable` accepts a pre-built `Dictionary<string, object>` variable for dynamic or programmatic argument supply.
- Output values from the DMN decision are written back into the output-direction entries of the `Arguments` dictionary.
- The `InfoBox` property is a designer-only text block used to surface contextual help; it has no runtime effect.
