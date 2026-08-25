---
confidence: medium
---

# Replace Text in Document — TargetInvocationException / Studio Crash on Drop

## Context

What this looks like:
- Studio errors **immediately when the `Replace Text in Document` / `Replace Text` activity is dropped** onto the designer panel, or while opening a workflow that contains it
- Error message contains `System.Reflection.TargetInvocationException` (often wrapping an inner type/version load error), or Studio becomes unstable / crashes

What can cause it:
- A **version mismatch between Studio and the `UiPath.Word.Activities` package** — an older Studio loading a newer package dependency (or vice versa) cannot construct the activity's designer, so the reflection call that instantiates it throws

What to look for:
- The Studio version vs the installed `UiPath.Word.Activities` version.
- Whether the crash is design-time (on drop / open) rather than at runtime.

## Investigation

1. Confirm the failure is **design-time** (on dropping the activity or opening the workflow in Studio), not a runtime job fault — this distinguishes it from the runtime "Cannot create unknown type" package gap.
2. Compare the installed `UiPath.Word.Activities` version against the Studio version's supported range.

## Resolution

- **If Studio and the package are mismatched** — open `Manage Packages`, select `UiPath.Word.Activities`, and upgrade or downgrade to a version compatible with the installed Studio (a known-stable release for that Studio version), then reopen the workflow.
- **If upgrading the package is required by other activities** — upgrade Studio to a version that supports the newer package instead, so the whole dependency set is compatible.

> This is a **design-time** Studio crash from a version mismatch. For the **runtime** `Cannot create unknown type WordApplicationScope` fault (the robot lacks the package version at execution), see [word-scope-cannot-create-unknown-type.md](./word-scope-cannot-create-unknown-type.md).
