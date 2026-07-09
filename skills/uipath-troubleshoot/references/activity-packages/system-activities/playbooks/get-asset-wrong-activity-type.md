---
confidence: high
---

# Get Asset Failed — Wrong Activity for Asset Type

## Context

A `Get Asset` or `Get Credential` activity failed because the activity type does not match the asset type in Orchestrator.

What this looks like:
- Error message contains `"does not work with assets of type Credential"` or `"Invalid asset type"`
- `Get Orchestrator Asset` used on a Credential asset, or `Get Credential` used on a Text/Integer/Boolean asset

What can cause it:
- Developer selected the wrong activity when building the workflow
- Asset type was changed in Orchestrator after the workflow was built

What to look for:
- The asset name from the faulted activity
- The asset type in Orchestrator (Text, Integer, Boolean, or Credential)

## Investigation

1. Identify the asset name from the faulted activity in the error message or job traces.
2. Verify the asset type in Orchestrator — navigate to the folder > Assets and inspect the Type column.
3. Confirm the workflow uses `Get Orchestrator Asset` when the asset is a Credential, or `Get Credential` when the asset is Text/Integer/Boolean.

## Resolution

- **If `Get Orchestrator Asset` on a Credential:** replace with `Get Orchestrator Credential`. Update downstream variable types — `Get Credential` returns a `SecureString` for the password and a `String` for the username.
- **If `Get Credential` on a Text/Integer/Boolean asset:** replace with `Get Orchestrator Asset` (or `Get Asset`).
