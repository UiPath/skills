---
confidence: high
---

# Invalid Status Code 400 — Argument Mismatch

## Context

What this looks like:
- HTTP 400 error
- "Argument values did not match definitions"

What can cause it:
- Arguments supplied do not match expected types or schema
- Incorrect number or order of arguments passed to a service task or API call

## Investigation

1. Compare the argument definitions in the workflow against what is being passed
2. Check argument types and order

## Resolution

- Fix argument definitions in the workflow or consuming activities to match the expected schema
- Validate payload structure before API or activity calls
