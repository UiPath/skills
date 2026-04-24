---
confidence: medium
---

# Expression Evaluation and Input Errors

## Context

What this looks like:
- Errors during evaluation of activity inputs
- Missing or null parameters at runtime
- Job faulted due to null input value during GUID parsing

What can cause it:
- Input arguments not passed from previous activities
- Null or empty values from data sources
- Incorrect variable assignments or missing default values
- Upstream activity failed to set or fetch a required value

What to look for:
- Check which activity input is failing
- Trace the data flow from the source activity to the failing activity
- Check for null checks on critical values

## Investigation

1. Identify the exact error and which input/variable is null or missing
2. Trace the input data flow through the workflow — which activity should have set the value
3. Check if the upstream activity completed successfully and produced the expected output
4. Check for default values on critical input arguments

## Resolution

- **If missing input:** fix the variable mapping between the source and consuming activities
- **If null value:** add null checks before parsing values such as GUIDs
- **If upstream failure:** fix the upstream activity that should have set the value
- **If no default:** set default values for critical input arguments
