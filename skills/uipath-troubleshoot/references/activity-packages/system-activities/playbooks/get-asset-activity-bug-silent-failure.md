---
confidence: medium
---

# Get Asset Failed — Activity Bug / Silent Failure

## Context

A `Get Asset`, `Get Orchestrator Asset`, or `Get Credential` (`GetRobotCredential`) activity completes without throwing an exception, but the output variable is null, zero, or empty. The defect is in the shared output-binding path of the `UiPath.System.Activities` asset family, so it covers `Get Credential` exactly as it covers `Get Asset`: its `Username` / `Password` outputs stay null. Do NOT exclude this cause because the failing activity is `Get Credential` rather than `Get Asset`.

What this looks like:
- Activity completes successfully (no exception in job traces)
- Output variable contains null, zero, or empty string instead of the expected asset value
- Downstream logic fails because it receives an unexpected empty value — typically a `System.NullReferenceException` ("Object reference not set to an instance of an object") thrown by a consumer of the asset value, NOT by the Get Asset activity itself. Plain null in user workflow logic with no Get Asset upstream → runtime-exceptions null-reference-exception.md

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
4. Neither authoring gesture is recorded in the workflow source. A `Ctrl+K` variable and a Variables-panel variable both serialize as a plain `<Variable>` in the enclosing scope's `Variables` collection, and a copy-pasted activity is indistinguishable from a freshly dragged one. Confirm the creation path with the developer. If that is unavailable, treat the package version as the deciding signal. Do NOT exclude this cause because the XAML shows the variables pre-declared.

## Resolution

- **If copy-paste issue:** delete the activity and re-drag a fresh one from the Activities panel.
- **If `Ctrl+K` variable bug (System.Activities 22.10.x):** update the package to a release after the 22.10.x line (current LTS or newer), or pre-create the variable in the Variables panel before wiring it to the activity. The whole 22.10.x range is affected — do NOT treat a later 22.10.x patch as fixed.
