---
confidence: medium
---

# Write CSV — "Cannot set unknown member"

## Context

What this looks like:
- `Write CSV` faults (often at load/compile, or on first execution) with `Cannot set unknown member '<Type>.<Property>'` — e.g. `Cannot set unknown member 'UiPath.Core.Activities.WriteCsvFile.<prop>'`.
- The workflow opens and runs fine on the **developer's** machine but fails on the **robot / execution server**.

What can cause it:
- **Activity-package version skew between dev and runtime.** The XAML sets a property that exists in the `UiPath.System.Activities` (or `UiPath.Excel.Activities`) version used to **build** the workflow, but the **robot/runtime** has a **different (usually older) version** of that package where the property does not exist. Deserializing the XAML then can't set the "unknown member" the older activity doesn't define.

What to look for:
- The package versions pinned in `project.json` vs the versions actually installed on the robot / execution server.
- Whether the failure is environment-specific (works on dev, fails on the robot) — the signature of a version mismatch, not a logic bug.

## Investigation

1. Read the error from job evidence; confirm it is `Cannot set unknown member ...` at `Write CSV` (a deserialization/version error), not a `CsvHelper` `Method not found`, a delimiter, an access, or an encoding error (those are other playbooks).
2. Read `project.json` `dependencies` and note the `UiPath.System.Activities` / `UiPath.Excel.Activities` versions the project targets.
3. Establish the versions installed on the robot/execution server (out-of-band if off-host) and compare — a runtime version older/different than `project.json` is the skew.

## Resolution

- **Align the runtime to the project:** install the **exact same** `UiPath.System.Activities` / `UiPath.Excel.Activities` versions on the robot/execution server as pinned in `project.json`, then re-run. Activity-package versions must match between build and runtime.
- **Or rebuild against the runtime's versions:** if the robot must stay on a specific version, set the project's dependencies to that version in **Manage Packages**, re-validate, and republish — so the XAML only sets members the runtime activity defines.
- **Confirm:** after the versions match, the property deserializes and the `Cannot set unknown member` error no longer occurs.
