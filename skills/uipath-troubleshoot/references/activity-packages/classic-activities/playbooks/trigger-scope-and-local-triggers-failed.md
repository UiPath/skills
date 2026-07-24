---
confidence: medium
---

# Trigger Scope & Local Triggers Failed

## Context

A trigger-based attended automation built on classic `UiPath.Core.Activities` trigger activities —
`Trigger Scope` (`UiPath.Core.Activities.TriggerScope`), `Run Local Triggers`, and the individual
triggers (Hotkey / Key Press / Click / Form Event) — failed to **compile, register its triggers, or
start/stop monitoring**. The fault is in the trigger *infrastructure* (generation, registration,
dependencies, lifecycle), not in a downstream activity the trigger later fires.

Route the neighbouring paths elsewhere:
- Classic `Start Triggers` (the workflow-invoker sense) / `Invoke Workflow File` **invoking a child
  workflow** that fails (file not found, argument name/type/direction mismatch, isolated/elevated/session
  validation, wrong parent `Sequence`, or the child workflow threw) → [invoke-workflow-failed.md](./invoke-workflow-failed.md).
- A trigger fired and the **action it launched** (a `Click` / `Type Into`) faulted → the relevant UI
  playbook ([ui-element-not-found.md](./ui-element-not-found.md), [ui-element-interaction-failed.md](./ui-element-interaction-failed.md), …).

> **Parallel/concurrent Trigger Scopes are supported.** `Run Local Triggers` itself generates a
> read-only workflow that runs all the project's triggers **in parallel** (`.local\generated\Triggers.Generated.xaml`),
> and `Trigger Scope` has a `Concurrent` scheduling mode. Do NOT diagnose "two Trigger Scopes running at
> once" as the fault by itself — that is the normal mechanism. The real trigger-lifecycle failure is
> *blocking* (below), not a concurrency limit.

What this looks like:
- Runtime error `Run Local Triggers: The .local\generated\Triggers.Generated.xaml workflow cannot be found`
  (or a "No triggers available" / trigger-registration error) — the generated trigger workflow is
  missing or stale.
- A duplicate-key error (`An item with the same key has already been added`) or triggers that silently
  fail to register.
- The automation **hangs**: execution enters a `Trigger Scope` and never proceeds, or a listener stays
  active after the flow should have ended.
- A **"Cannot upgrade the legacy UiPath.Core.Activities package"** dependency error at load/publish.
- A Hotkey Trigger reports it cannot bind / listen at run time.

What can cause it:
1. **Missing or stale `.local\generated\Triggers.Generated.xaml`.** `Run Local Triggers` relies on a
   read-only workflow Studio auto-generates in the hidden `.local` cache. `.local` is a design-time
   cache that is not normally committed, so a **cloned/shared** project can lack it; a **stale/corrupt**
   cache, or a **Studio ↔ Assistant version mismatch after an upgrade**, produces the same
   "workflow cannot be found" at run time.
2. **Duplicate `TriggerId` or mismatched Form field key.** Copy-pasting triggers or form components
   reuses hidden `TriggerId`s, or leaves a Form Event / Trigger Form Button trigger's Button Key not
   matching the form component's field key → trigger registration fails (duplicate-key /
   "No triggers available").
3. **Trigger Scope lifecycle — blocking, not a concurrency limit.** A `Trigger Scope` in a sequential
   path does not "pass through": execution stays inside it and later activities never run. A
   `Trigger Scope` on a `Parallel` branch keeps its listener alive after the sibling branch finishes,
   and `Stop Trigger` / a boolean flag may not halt it (modern Trigger Scope has no timeout). This is a
   **design/lifecycle** problem, not "parallel scopes are forbidden."
4. **Legacy package conflict.** A pre-2018.3 process is normally remapped by the migration
   meta-package onto `UiPath.System.Activities` + `UiPath.UIAutomation.Activities`. But a legacy
   `UiPath.Core.Activities` package **published on a custom feed / Orchestrator** is installed instead
   and conflicts → "Cannot upgrade the legacy UiPath.Core.Activities package".
5. **Hotkey registration blocked.** A system-wide Hotkey Trigger combination is already claimed by
   another running application, so it cannot bind.

What to look for:
- Whether `.local\generated\Triggers.Generated.xaml` exists in the project, and whether `.local` was
  cloned/shared or the error followed a Studio/Assistant upgrade. Source-required.
- `TriggerId` values across triggers (uniqueness) and Form Button trigger Button Key vs. the form
  component field key. Source-required.
- Trigger lifecycle: a `Trigger Scope` on a sequential path with activities after it, or on a `Parallel`
  branch with no working stop path (`Stop Local Triggers` / `Stop Trigger` / gate variable).
- `project.json` dependencies: a lone legacy `UiPath.Core.Activities` entry vs. the modern
  `UiPath.System.Activities` + `UiPath.UIAutomation.Activities` split; and whether that legacy package
  exists on a custom feed / Orchestrator.
- The Hotkey Trigger's `Key` / `KeyModifiers` and whether another app owns that combination.

## Investigation

1. Classify the fault: **generated-file missing** (`Triggers.Generated.xaml` not found), **registration**
   (duplicate key / no triggers), **lifecycle hang** (stuck in / never stops monitoring), **legacy
   package** (cannot upgrade), or **hotkey bind**. Fetch Error logs.
2. When the error names the generated file, confirm whether `.local\generated\Triggers.Generated.xaml`
   exists, and whether the project was cloned/shared without `.local` or the error followed an upgrade.
3. In source, check `TriggerId` uniqueness and Form Button trigger Button Key ↔ form field key alignment.
4. For a hang, trace the `Trigger Scope` placement and its stop path (`Stop Local Triggers` / `Stop
   Trigger` / gate variable); remember concurrency itself is not the fault.
5. Read `project.json` dependencies for a legacy `UiPath.Core.Activities` package, and check whether it
   is published on a custom feed / Orchestrator.
6. For a hotkey failure, identify the `Key`/`KeyModifiers` and whether another app already claims it.

## Resolution

- **Missing / stale generated file:** reopen (or rebuild) the project in Studio so it regenerates
  `.local\generated\Triggers.Generated.xaml`; if the cache is stale/corrupt, delete the `.local` folder
  first, then reopen. Republish for the robot/Assistant. If the error followed a Studio/Assistant
  upgrade, align their versions and republish. Do NOT hand-edit or hand-create the generated file.
- **Duplicate `TriggerId` / mismatched field key:** give every trigger a unique `TriggerId`; align each
  Form Event / Trigger Form Button trigger's Button Key with the form component's field key.
- **Trigger Scope lifecycle / hang:** manage the lifecycle explicitly — use `Stop Local Triggers` /
  `Stop Trigger`, or an external boolean gate on a monitoring loop, to end monitoring; prefer
  `Run Local Triggers` (it generates and manages the concurrent trigger set for you) over hand-wiring
  multiple `Trigger Scope`s. Concurrency is not the defect — the missing/blocked stop path is.
- **Legacy package conflict:** remove the legacy `UiPath.Core.Activities` package from the custom feed
  (and Orchestrator) so the migration meta-package remaps to the modern split packages
  (`UiPath.System.Activities` + `UiPath.UIAutomation.Activities`); or rebuild on a clean modern template.
- **Hotkey registration blocked:** free the combination (close the app that owns it) or choose an
  unused / obscure multi-key combination (e.g. `Ctrl+Shift+Alt+<Key>`); `UseWindowsHotKey` switches the
  delivery method if the default driver approach is being intercepted.
- **Verify after fixing.** Re-validate (`uip rpa validate --file-path "<FILE_PATH>" --output json`, or
  validate in Studio) and re-run; confirm the triggers register and monitoring starts/stops as intended.
