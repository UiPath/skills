---
confidence: medium
---

# Get Asset Failed — Activity Bug / Silent Failure

## Context

A `Get Asset` or `Get Orchestrator Asset` activity completes without throwing an exception, but the output variable is null, zero, or empty.

What this looks like:
- Activity completes successfully (no exception in job traces)
- Output variable contains null, zero, or empty string instead of the expected asset value
- Downstream logic fails because it receives an unexpected empty value

What can cause it:
- Activity was copy-pasted from another sequence — copy-paste retains internal state from the original activity
- `UiPath.System.Activities` package version 22.10.x has a bug where variables created with `Ctrl+K` do not receive output values
- Output variable was created via `Ctrl+K` during activity configuration in the affected version

What to look for:
- Whether the activity was copy-pasted from another sequence
- The `UiPath.System.Activities` package version (especially 22.10.x)
- How the output variable was created (pre-created in Variables panel vs `Ctrl+K`)

## Investigation

1. Check whether the activity was copy-pasted from another sequence — copy-paste retains internal state from the original.
2. Check the Studio and `UiPath.System.Activities` package version — version 22.10.x has a bug where variables created with `Ctrl+K` do not receive output values.
3. Verify the output variable was created before the activity (not via `Ctrl+K` during activity configuration in the affected version).

## Resolution

- **If copy-paste issue:** delete the activity and re-drag a fresh one from the Activities panel.
- **If `Ctrl+K` variable bug (System.Activities 22.10.x):** update the package to ≥22.10.4, or pre-create the variable in the Variables panel before wiring it to the activity.
