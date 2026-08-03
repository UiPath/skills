---
confidence: medium
---

# Variable and Expression Errors

## Context

What this looks like:
- "Missing output variables"
- "Assignments are not allowed in expressions"
- "Failed to evaluate the input collection variable"
- Exclusive gateway conditions not matching expected values

Not this playbook:
- `Failed to evaluate the input collection variable for the marker element` with code `400008`: `InvalidCastException` + `ExpressionList` → [marker-invalid-cast](marker-invalid-cast.md); other marker failures (size, null items, non-array) → [multi-instance-parallel](multi-instance-parallel.md). Use this playbook for that message only when no marker element is involved
- Codes `400300`/`400301`/`400302` or `Property 'X' not found against object of type ExpressionDictionary` → [expression-evaluation-errors](expression-evaluation-errors.md)
- Gateway raises `400001` (`No outgoing flow condition met`) → [gateway-no-outgoing-flow](gateway-no-outgoing-flow.md); this playbook covers conditions that evaluate but match the wrong branch (case mismatch, emoji)
- `<api> is not defined` naming a browser API (btoa, atob, TextEncoder) → [js-runtime-discrepancy](js-runtime-discrepancy.md)

What can cause it:
- Drag/drop swimlane bug — moving task nodes in swimlanes can clear root-level variable references
- Variable name case sensitivity in exclusive gateway conditions (e.g., "customer" vs "Customer")
- Emoji characters in condition expressions causing evaluation failures
- Salesforce Execute Connector SOQL "=" operator falsely flagged as assignment (fixed in later releases)
- Sub-process variable propagation — error detail and category fields may not propagate to parent process (known limitation, check latest release notes)

What to look for:
- Check which expression or variable is failing
- Check if task nodes were recently moved between swimlanes
- Check for case mismatches in gateway conditions

## Investigation

1. Identify the exact error message and which variable/expression is affected
2. Check if the variable exists at the root level of the BPMN process
3. For gateway conditions: compare variable names case-sensitively against the condition expression
4. Check for special characters (emoji, unicode) in expressions
5. For sub-process variables: check if error detail/category fields are expected in the parent process

## Resolution

- **If missing variable references:** re-create the output variable references on the affected task node
- **If case mismatch:** fix the variable name or condition expression to match exactly
- **If emoji/special characters:** remove special characters from expressions
- **If SOQL assignment error:** update to the latest version or rewrite the filter expression
