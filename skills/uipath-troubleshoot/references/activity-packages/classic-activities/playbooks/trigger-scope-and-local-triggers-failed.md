---
confidence: medium
---

# Trigger Scope & Local Triggers Failed

## Context

A trigger-based automation built on classic `UiPath.Core.Activities` trigger activities — `Trigger Scope`
(Monitor Events), `Run Local Triggers`, hotkey / click / key-press triggers, or a `Start Job` launched
from a trigger — failed to **compile, register its hooks, or start monitoring**. The fault is in the
trigger *infrastructure* (generation, registration, dependencies), not in a downstream activity the
trigger later fires.

Route the neighbouring paths elsewhere:
- Classic `Start Triggers` / `Invoke Workflow File` **invoking a child workflow** that fails (workflow
  file not found, argument name/type/direction mismatch, isolated/elevated/session validation, wrong
  parent `Sequence`, or the child workflow itself threw) → [invoke-workflow-failed.md](./invoke-workflow-failed.md).
- A trigger fired and the **action it launched** (a `Click` / `Type Into`) faulted → the relevant UI
  playbook ([ui-element-not-found.md](./ui-element-not-found.md), [ui-element-interaction-failed.md](./ui-element-interaction-failed.md), …).

What this looks like:
- Studio compile / validation error naming a **missing generated file under `.local\generated\`**, or a
  **duplicate-ID / duplicate-entry-point** error.
- Job / instance faults **immediately** on start (seconds), before any business step, with a
  trigger-registration or monitoring exception.
- A **"Cannot upgrade legacy UiPath.Core.Activities"** dependency error when opening/migrating an old
  project.
- A hotkey trigger reports at run time that it **cannot listen / start**.

What can cause it:
1. **Missing or corrupt `.local\generated\Triggers.Generated.xaml`.** `Run Local Triggers` relies on a
   background workflow Studio auto-generates in the hidden `.local` cache to track local events.
   Cloning / code-sharing that omitted (or corrupted) `.local` leaves that generated workflow absent →
   compile or run fails referencing it.
2. **Duplicate entry point or duplicate Trigger IDs.** Copy-pasting actions/forms duplicates hidden
   Unique IDs / Field Keys / `TriggerId`s. Studio then tries to register two identical triggers at once →
   execution crashes.
3. **Trigger Scopes split across a `Parallel`.** Separate `Trigger Scope` blocks placed in a standard
   `Parallel` container cannot both register their hooks — the local robot service allows only **one**
   active monitoring session, so the second scope halts execution the instant it starts.
4. **Legacy package conflict.** A pre-2018.3 process still carrying the old monolithic
   `UiPath.Core.Activities` package conflicts with the modern split dependencies
   (`UiPath.System.Activities` + `UiPath.UIAutomation.Activities`) → "Cannot upgrade legacy
   UiPath.Core.Activities".
5. **Local hotkey registration blocked.** Another running application already owns that key combination,
   so the hotkey trigger cannot bind / listen.

What to look for:
- Project layout: presence of `.local\generated\Triggers.Generated.xaml`; whether `.local` was
  committed/cloned. Source-required.
- Workflow structure around trigger activities: a `Parallel` containing **more than one** `Trigger Scope`;
  duplicated `TriggerId` / Field Key values across actions or forms. Source-required.
- `project.json` dependencies: a lone legacy `UiPath.Core.Activities` entry vs. the modern
  `UiPath.System.Activities` + `UiPath.UIAutomation.Activities` split.
- The immediate-fault error text: which `Trigger Scope` / hotkey failed to register, and whether a
  `Parallel` appears on the stack.

## Investigation

1. Classify the fault: **compile** error (missing generated file / duplicate ID / legacy package) vs.
   **runtime** immediate fault (registration / monitoring exception). Fetch Error logs.
2. Locate the trigger activities in source. Check for: more than one `Trigger Scope` inside a `Parallel`;
   duplicated `TriggerId` / Field Key; `Run Local Triggers` usage.
3. When `Run Local Triggers` is used and the error names a generated/local file, confirm whether
   `.local\generated\Triggers.Generated.xaml` exists.
4. Read `project.json` dependencies for a legacy `UiPath.Core.Activities` package.
5. For a hotkey failure, identify the key combination and whether another app already claims it.

## Resolution

- **Missing / corrupt generated file:** close the project in Studio, delete the hidden `.local` folder
  from the project directory, reopen in Studio — Studio re-compiles and regenerates
  `Triggers.Generated.xaml`. Do NOT hand-edit or hand-create that file.
- **Duplicate entry point / Trigger IDs:** open the Form Designer / trigger properties panel and give
  every action element a unique Field Key / `TriggerId`; remove the duplicated entry point.
- **Split Trigger Scopes in a `Parallel`:** consolidate — place all trigger elements (hotkey, click,
  form) inside a **single** shared `Trigger Scope` instead of breaking them into separate scopes under a
  `Parallel`.
- **Legacy package conflict:** remove the legacy `UiPath.Core.Activities` package from the feed /
  dependencies and migrate onto the modern split packages (`UiPath.System.Activities` +
  `UiPath.UIAutomation.Activities`) — rebuild on a clean modern template rather than upgrading in place.
- **Hotkey registration blocked:** close the app holding the key bind, or change the trigger to an
  unused, obscure multi-key combination (e.g. `Ctrl+Shift+Alt+<Key>`).
- **Verify after fixing.** Re-validate (`uip rpa validate --file-path "<FILE_PATH>" --output json`, or
  validate in Studio) and re-run; confirm the `Trigger Scope` registers and monitoring starts.
