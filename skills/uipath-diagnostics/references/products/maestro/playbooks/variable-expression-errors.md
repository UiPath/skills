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

What can cause it:
- Drag/drop swimlane bug — moving task nodes in swimlanes can clear root-level variable references
- Variable name case sensitivity in exclusive gateway conditions (e.g., "customer" vs "Customer")
- Emoji characters in condition expressions causing evaluation failures
- Salesforce Execute Connector SOQL "=" operator falsely flagged as assignment (hotfix in S188.1)
- Sub-process variable propagation — error detail and category fields may not propagate to parent process (fix via MST-7284)

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
- **If SOQL assignment error:** update to S188.1 hotfix or rewrite the filter expression
