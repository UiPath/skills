---
confidence: medium
---

# Invoke Workflow / Start Triggers Failed

## Context

`Invoke Workflow File` (or `Start Triggers`, which invokes a workflow) faulted. The failure can be in
locating the workflow, in passing arguments, in the session/isolation configuration, or inside the
invoked child workflow itself.

What this looks like:
- The invoked workflow file cannot be found or loaded at run time
- An argument mismatch — the arguments passed do not match the invoked workflow's argument names,
  types, or directions
- A validation error about isolated / elevated / target-session settings (e.g. a non-current target
  session or elevated execution requires isolated execution)
- An error that persistence is not supported in the current runtime
- The child workflow ran and threw its own exception, which propagates up through the invoke

What can cause it:
- The workflow file path is wrong on the robot machine, or the `.xaml` was not published/included in
  the package
- Argument names/types/directions drifted between the caller and the invoked workflow (a renamed or
  retyped argument)
- Isolated/elevated/target-session options set in a combination the runtime does not allow
- A `Start Triggers` placed somewhere other than directly inside a `Sequence` (its parent constraint)
- The real error is inside the child workflow — the invoke is just the propagation point

What to look for:
- The invoked workflow path and whether it exists in the published package on the robot
- The argument list on the invoke vs the invoked workflow's declared arguments
- The isolated/elevated/target-session settings on the invoke
- Whether the stack/inner exception points inside the child workflow rather than the invoke itself

## Investigation

1. Identify the invoke activity and the workflow file it targets; confirm that file is present in the
   running package on the robot.
2. Compare the arguments passed against the invoked workflow's declared arguments (name, type,
   direction).
3. Inspect the isolated / elevated / target-session settings for an unsupported combination.
4. For `Start Triggers`, confirm it sits directly inside a `Sequence`.
5. Read the inner/innermost exception — if it originates inside the child workflow, switch the
   investigation to that activity/playbook.

## Resolution

- **If the workflow file is missing:** correct the path, or ensure the `.xaml` is included in the
  published package.
- **If arguments mismatch:** align the invoke's arguments with the invoked workflow's declared
  arguments (names, types, in/out directions).
- **If isolated/elevated/session settings are invalid:** set a supported combination (e.g. enable
  isolated execution when required by elevated/non-current-session options).
- **If `Start Triggers` has the wrong parent:** place it directly inside a `Sequence`.
- **If the child workflow threw:** diagnose the failing activity inside the child workflow using its
  own signature/playbook; the invoke is only relaying the error.
