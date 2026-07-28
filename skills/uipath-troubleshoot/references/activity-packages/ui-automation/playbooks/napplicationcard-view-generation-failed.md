---
confidence: high
---

# NApplicationCard — Could Not Generate View (Design-Time / Studio)

## Context

A workflow containing a `Use Application/Browser` scope (the `NApplicationCard` activity,
`UiPath.UIAutomationNext.Activities.NApplicationCard`) fails to **render on the Studio design surface**
— when the file is opened, or when Studio validates/builds it. This is a design-time / Studio failure,
NOT a faulted robot job: there is no Orchestrator job, log, or trace, and the error surfaces in the
Studio Output panel or as a broken activity card in the designer.

What this looks like:
- `Could not generate view for NApplicationCard` (the activity renders as a red/broken card in the
  designer, or the whole workflow refuses to open).
- `Object reference not set to an instance of an object.` raised while opening or validating a
  workflow that contains a `Use Application/Browser` scope (design-time NullReferenceException from the
  activity's view factory, not a robot exception).
- The failure appears at design time in Studio — not while a job runs. No job key, no robot log.

This is distinct from the **runtime** NApplicationCard faults — for those use the sibling playbooks:
- Scope tried to launch the app and failed → [application-open-failed.md](./application-open-failed.md)
  (`ApplicationOpenException`).
- Scope with `OpenMode=Never` couldn't find the app → [application-not-found.md](./application-not-found.md)
  (`ApplicationNotFoundException`).
- Browser scope reached the browser but the automation channel is broken →
  [browser-communication-failed.md](./browser-communication-failed.md).

What can cause it:
- **Studio ↔ activity-package version skew.** The Studio application was updated or downgraded
  independently of the automation package suite, so the `NApplicationCard` designer view shipped with
  Studio no longer matches the `UiPath.UIAutomation.Activities` / `UIAutomationNext` version pinned in
  the project. The view factory cannot render the card.
- **Corrupted local activity / package cache.** The downloaded-activity/NuGet cache under
  `%LOCALAPPDATA%\UiPath\.cache` broke (partial download, interrupted upgrade), so Studio loads an
  inconsistent copy of the activity assembly.
- **Stale project cache.** Leftover `.local` / `bin` / `obj` build artifacts from prior debug runs
  drifted from the current dependency set.

What to look for:
- The error occurs on **open/validate in Studio**, not during a run — confirm there is no faulted job.
- `project.json` dependency pins for `UiPath.UIAutomation.Activities` (and/or `UIAutomationNext`)
  versus the installed Studio version (`studioVersion` in `project.json` is the version that last
  saved the project).
- Presence of stale `.local` / `bin` / `obj` folders, and whether the machine's Studio version changed
  recently (update/downgrade) relative to when the project last opened cleanly.

## Investigation

1. Confirm this is design-time: there is no Orchestrator job / robot log / trace for the failure — the
   error is in Studio's Output panel or the designer surface when the workflow is opened.
2. Open `project.json` and read the `UiPath.UIAutomation.Activities` / `UIAutomationNext` version pin
   and the `studioVersion` field. Note whether the activity package version is far from what the
   current Studio ships/supports (a skew after a Studio update or downgrade).
3. Check for stale caches: `.local` / `bin` / `obj` in the project, and whether
   `%LOCALAPPDATA%\UiPath\.cache` may hold a broken activity-package copy.
4. Confirm the `.xaml` itself is structurally intact (the `NApplicationCard` node is present and
   well-formed) — a rendering failure with valid source points at cache/version skew, not corrupt XAML.

## Resolution

- **Version skew (most common):** align the automation activity package with the Studio version and
  runtime engine. Close Studio; reopen the project; in **Manage Packages** set
  `UiPath.UIAutomation.Activities` to a version compatible with the installed Studio and the runtime
  engine — update it to match a newer Studio, or downgrade to the last stable version that matches the
  Studio you are on. Do not mix a Studio build with an activity-package version it does not support.
- **Corrupted activity/package cache:** close Studio and clear the package cache at
  `%LOCALAPPDATA%\UiPath\.cache`, then reopen so Studio re-downloads a clean copy of the activity
  package.
- **Stale project cache:** with Studio closed, delete the project's `.local` folder (deleting `bin`
  and `obj` is also safe), then reopen the project to rebuild.
- After clearing caches / aligning versions, reopen the workflow — the `NApplicationCard` view
  regenerates once Studio loads a consistent activity assembly.

Do not attempt to fix this by editing the `.xaml` by hand — the source is intact; the fault is in the
Studio-side view factory / cache, and hand-edits risk corrupting a valid file.
