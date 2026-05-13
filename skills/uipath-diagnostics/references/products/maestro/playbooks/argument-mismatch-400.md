---
confidence: medium
---

# Invalid Status Code 400 — Argument Mismatch

## Context

What this looks like:
- HTTP 400 with `Argument values did not match definitions` or similar
- Often a sibling of the more specific top-20 errors:
  - [input-schema-mismatch](input-schema-mismatch.md) — full payload schema mismatch on workflow/agent start
  - [missing-required-parameter](missing-required-parameter.md) — a single named required field is absent

What can cause it:
- Arguments do not match the consuming activity's expected types or schema
- Wrong number or order of arguments passed to a service task or API call
- A workflow input renamed without updating callers

What to look for:
- Whether the error names a single field (→ [missing-required-parameter](missing-required-parameter.md))
- Whether the error mentions schema conformance broadly (→ [input-schema-mismatch](input-schema-mismatch.md))
- Otherwise, the activity's argument signature vs what's being passed

## Investigation

1. Get the incident: `uip maestro instance incidents <instance-id> -f <folder-key> --output json`
2. Pull the inputs sent to the failing activity: `uip maestro instance variables <instance-id> -f <folder-key> --parent-element-id <element-id> --output json`
3. Compare against the activity's argument definitions in the BPMN: `uip maestro instance asset <instance-id> -f <folder-key> --output json`

## Resolution

- Fix the argument mapping in the workflow or consuming activity to match the expected definitions
- Validate payload structure (types, order, names) before API or activity calls
- For more specific failures, route to [input-schema-mismatch](input-schema-mismatch.md) or [missing-required-parameter](missing-required-parameter.md)
