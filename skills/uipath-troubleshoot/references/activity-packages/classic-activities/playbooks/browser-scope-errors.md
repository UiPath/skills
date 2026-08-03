---
confidence: medium
---

# BrowserScope (Attach Browser) Errors

## Context

The classic `UiPath.Core.Activities.BrowserScope` activity — the **Attach Browser** container in the
classic design experience (`UiPath.UIAutomation.Activities`) — failed to attach to, communicate with,
or run children against a browser. This playbook owns the **COM / environmental** BrowserScope
failure family (`COMException`, `HRESULT E_FAIL`, "Invalid access to memory location") and routes the
two adjacent families to their existing homes.

Three signatures reach BrowserScope. Route by the leaf signal:

1. **"Cannot communicate with the browser"** — the robot reached the browser but lost the extension
   channel. Corrupted/missing browser extension, stray background browser processes, or the browser
   running under a different user profile than the robot. → Extension/comms failures are the
   `BrowserOperationException` family: see
   [browser-open-or-attach-failed.md](./browser-open-or-attach-failed.md). This playbook does not
   duplicate that content.
2. **"Timeout reached" / `SelectorNotFoundException`** — the window/tab title changed dynamically so
   the scope's top-level selector no longer matches, or a custom `TimeoutMS` is being ignored after a
   legacy `UiPath.UIAutomation.Activities` package migration (the value silently falls back to the
   default ~30 s). → Selector drift / scope-attach-target failures:
   [ui-element-not-found.md](./ui-element-not-found.md). Full-timeout waits with no element:
   [ui-activity-timeout.md](./ui-activity-timeout.md). The package-migration `TimeoutMS`-fallback is
   documented under *What can cause it* below because it is BrowserScope-specific.
3. **`COMException` — "Invalid access to memory location" (`0x800703E6`) or `HRESULT E_FAIL`
   (`0x80004005`)** — a `System.Runtime.InteropServices.COMException` from the classic browser engine.
   This is an **environmental** conflict between UiPath's background COM engine and the OS the robot
   runs on, **owned by this playbook.** It is NOT a selector, extension, or flow-ordering problem — the
   selector and extension can be perfectly valid and it still throws.

What the COM/environmental signature looks like:
- `System.Runtime.InteropServices.COMException`, with one of these messages:
  - "Invalid access to memory location." — `Exception from HRESULT: 0x800703E6`
  - "Error HRESULT E_FAIL has been returned from a call to a COM component." — `0x80004005`
- surfaced at a `BrowserScope` / `Attach Browser` activity
- The same workflow runs clean on the developer machine (attended) but throws on the unattended
  production robot, or throws only after an OS/session/display change
- The fault fires at scope startup, before any child activity's selector is evaluated

What can cause the COM/environmental family:
- **Display-scaling mismatch** — the development machine and the production/Orchestrator runtime run
  at different display-scaling (DPI) settings, so the classic engine's coordinate/marshalling
  assumptions break against the browser's render surface.
- **Privilege / integrity-level mismatch** — the browser and UiPath (Robot/Studio) run at different
  user-access levels (one elevated, one not), so the COM engine cannot access the browser's memory
  across the integrity boundary.
- **Unattended / non-interactive session constraints** — an unattended robot in a Session-0-style or
  disconnected/locked session cannot give the classic browser engine the interactive desktop it needs.
- General environmental drift between the machine the automation was authored on and the machine it
  runs on (OS build, GPU/rendering stack, security software hooking COM).

What can cause the package-migration `TimeoutMS` fallback (family 2, BrowserScope-specific):
- After a legacy `UiPath.UIAutomation.Activities` version update, a custom `TimeoutMS` set on the
  scope/child is ignored and silently reverts to the default (~30 s). The activity then times out at
  ~30 s even though a longer timeout is configured — the mismatch between the *configured* timeout and
  the *observed* ~30 s duration is the tell.

What to look for:
- The exact exception FQN and `HRESULT` on the failing scope — `COMException` + `E_FAIL` /
  `0x80004005` routes here; `BrowserOperationException` routes to browser-open-or-attach-failed.md;
  `SelectorNotFoundException` / `ActivityTimeoutException` routes to the selector/timeout playbooks.
- Whether the failure is environment-specific: works on dev, fails on the prod robot (or vice versa),
  or started after a machine/OS/session change.
- The robot's session type (attended vs unattended, interactive vs Session-0) and run privilege.
- For the timeout tell: the configured `TimeoutMS` vs the observed activity duration.

## Investigation

1. Identify the failing activity and confirm it is a classic `BrowserScope` / `Attach Browser`
   (`UiPath.Core.Activities.BrowserScope`). Extract the leaf exception FQN, message, and `HRESULT`
   from the job logs / `jobs get` error surface.
2. **Route on the leaf signal:**
   - `COMException` + `E_FAIL` / `0x80004005` / "Invalid access to memory location" → continue here
     (environmental family).
   - `BrowserOperationException` / "cannot communicate with the browser" / extension-related →
     [browser-open-or-attach-failed.md](./browser-open-or-attach-failed.md).
   - `SelectorNotFoundException` → [ui-element-not-found.md](./ui-element-not-found.md);
     `ActivityTimeoutException` → [ui-activity-timeout.md](./ui-activity-timeout.md).
3. For the COM/environmental family, establish the **environment delta**: on which machine/session did
   it succeed vs fail? Check the job's `HostMachineName`, `Type` (Attended/Unattended), and
   `RuntimeType` against where the workflow was authored/last worked.
4. Check for a **display-scaling** difference between the authoring machine and the runtime machine.
5. Check for a **privilege / integrity-level** difference — is the browser (or the robot) run
   elevated on one machine and not the other?
6. Confirm the robot session was interactive and unlocked for an unattended run (a Session-0 or
   locked/disconnected session cannot host the classic browser engine).
7. For the timeout tell (family 2): compare the configured `TimeoutMS` on the scope/child against the
   observed activity duration in the logs; a ~30 s duration under a longer configured timeout after a
   package update points to the migration fallback.

## Resolution

- **If display scaling differs between dev and runtime:** match display-scaling (DPI) settings across
  the development machine and the production/Orchestrator runtime so the classic engine's coordinate
  assumptions hold.
- **If browser and UiPath run at different privilege levels:** run the browser and UiPath
  (Robot/Studio) at the **same** user-access level — do not mix elevated and non-elevated.
- **If the unattended session is non-interactive:** run the process in an interactive, unlocked
  session with a real desktop; do not host classic browser automation in a Session-0 context.
- **If a custom `TimeoutMS` is being ignored after a package migration:** update the
  `UiPath.UIAutomation.Activities` dependency (Manage Packages) to a version where the custom timeout
  is honored, then re-validate that the configured timeout takes effect.
- **If the app loads tracking scripts slowly and `Complete` readiness never settles:** set the child's
  `WaitForReady` to `None` or `Interactive` instead of `Complete`.
- **Strategic (recommended):** `BrowserScope` / Attach Browser belongs to the **classic** design
  experience. Migrate to the modern **Use Application/Browser** container — it uses unified targets and
  handles background crashes and container exceptions natively, eliminating most classic COM/marshalling
  faults. Migrating is the durable fix when environmental faults recur; the alignment steps above are
  the immediate fix for the current run.

> **Approval gate.** Environment/privilege/display-scaling changes and package updates are
> recommendations for the user or platform team — present the exact steps; do not apply them. A source
> change (e.g. migrating to Use Application/Browser, editing `WaitForReady`) follows the SKILL.md
> approval gate: present the diff, get approval, delegate the edit to `uipath-rpa`.
