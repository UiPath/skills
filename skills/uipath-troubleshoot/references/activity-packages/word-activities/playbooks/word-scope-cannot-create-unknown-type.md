---
confidence: high
---

# Word Application Scope — "Cannot create unknown type WordApplicationScope"

## Context

What this looks like:
- The workflow fails to load or compile with `Cannot create unknown type '{clr-namespace:UiPath.Word.Activities;assembly=UiPath.Word.Activities}WordApplicationScope'` (or a similar "unknown type" / "could not load activity" error)
- The failure happens before any document is touched — at job start or during package restore, not at runtime inside the scope

What can cause it:
- The machine executing the job **lacks the `UiPath.Word.Activities` package dependency**, or has a version that does not contain the `WordApplicationScope` type. The XAML references the activity, but the assembly is not restored on that host.
- **Version mismatch across environments** — the package resolves locally in Studio but a different (or missing) version is installed on the remote/unattended robot via Orchestrator, so the type cannot be created there.

What to look for:
- `project.json` lists `UiPath.Word.Activities` but the robot's package cache / feed does not have that version.
- Works in Studio, fails only when run via Orchestrator on a remote robot.

## Investigation

1. Open `Manage Packages` in Studio and confirm `UiPath.Word.Activities` is installed and referenced. Compare the resolved version against `project.json`.
2. If the job runs via Orchestrator on a remote robot, confirm the same `UiPath.Word.Activities` version is available on that robot — check the robot's package feed and that the published package bundled the dependency.

## Resolution

- **If the package is missing or out of date in Studio** — install / update `UiPath.Word.Activities` via `Manage Packages`, rebuild, and re-publish.
- **If the version differs across environments** — pin the dependency version in `project.json` and confirm that exact version is published to the feed the robot restores from, so versions match perfectly across Studio and every robot.
- **If running on a remote robot** — confirm the robot can reach the package feed and that the published process bundled `UiPath.Word.Activities`; republish if the dependency was not included.
