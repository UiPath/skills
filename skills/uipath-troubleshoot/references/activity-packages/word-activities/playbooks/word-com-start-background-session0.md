---
confidence: medium
---

# Word Application Scope — COM Start Fails in Background / Session 0 (unattended)

## Context

What this looks like:
- `Word Application Scope` / `Use Word File` faults on **COM start**, before any document is opened.
- Exception type `UiPath.Word.WordException`, message `Error opening document, make sure Word application is installed. If already installed, an Office Repair may be required.`
- Stack runs through the COM-start path:
  - `UiPath.Word.Windows.Utilities.WordAppHelpers.StartNewApplication`
  - `UiPath.Word.Windows.Utilities.ComAppReferenceCountManager.StartOrAttach`
  - `UiPath.Word.Activities.WordApplicationScope.Execute`
- The job is typically **unattended** (Orchestrator-dispatched on a robot machine). A common tell: Word opens fine when a user launches it interactively on the same machine, but the unattended robot fails.
- Distinct from the open-path `COMException "Command failed"` (faults on `Documents.Open`; see [word-open-sharepoint-url-com-command-failed.md](./word-open-sharepoint-url-com-command-failed.md)) and from the wrong-thread cast (`0x8001010E`; see [word-export-pdf-com-wrong-thread.md](./word-export-pdf-com-wrong-thread.md)).

What can cause it (more than one may apply):
- **Background Process / Session 0 (primary).** The process is published as a Background Process, so on an Unattended Robot it runs in **Session 0** under `LOCAL SERVICE` with no interactive desktop. Microsoft Office apps (Word/Excel/PowerPoint) are user-session apps — their COM server can only instantiate inside an interactive Windows session, so `StartNewApplication` fails. The project-side marker is `runtimeOptions.requiresUserInteraction: false` in `project.json` (equivalently, **Project Settings → Starts in Background = Yes**). **Note: modern `project.json` has no `"background": true` key — `requiresUserInteraction: false` is the flag.**
- **Word not installed / not COM-capable** on the robot machine — no supported Word desktop edition, or a non-interop install. The error's first clause ("make sure Word application is installed") points here; confirmed only when Word does *not* open interactively for the robot user.
- **Broken Office COM Interop registration** — install/uninstall/downgrade or component (e.g. Skype for Business) mismatch left Word mis-registered; needs an Office Repair. This fails **both** interactively and unattended, so it is ruled out when Word opens cleanly in an interactive session.

What to look for:
- `runtimeOptions.requiresUserInteraction` in `project.json` (`false` ⇒ background process).
- Whether the run is unattended Session 0 / background vs attended / interactive.
- Whether Word opens standalone for the robot user on the affected machine (host-side check).

## Investigation

1. Read the error from job evidence. Confirm the type is `UiPath.Word.WordException` with the "make sure Word application is installed … Office Repair may be required" text and the top frame is `WordAppHelpers.StartNewApplication` (COM start) — not `Documents.Open` and not a child cast.
2. Read `runtimeOptions.requiresUserInteraction` from `project.json`. `false` confirms the process is a Background Process that runs in Session 0 when unattended. Do NOT look for a `"background": true` key — it does not exist in modern `project.json`.
3. Establish the run surface: unattended Orchestrator job in background / Session 0 vs attended / interactive session. The job's robot/machine and session type are in the job evidence.
4. Host-side discriminators (out-of-band — ask the user, not reachable via CLI): (a) Does a supported Word desktop edition open standalone for the robot user (`Win+R → winword`)? (b) Does the Studio Repair Tool for Microsoft Office *detect* Word? Answers split the causes:
   - Word **opens interactively** but the **background** robot fails ⇒ Background/Session-0 limitation (primary cause).
   - Word **does not open** / is absent ⇒ not installed.
   - Word **errors interactively too** / Repair detects a problem ⇒ broken registration.

## Resolution

- **If `requiresUserInteraction: false` / Background Process / Session 0 (Word opens interactively):**
  - Publish the process as a **foreground** process: Studio **Project Settings → Starts in Background → No** (sets `runtimeOptions.requiresUserInteraction: true`), so the Office activities run in an interactive session.
  - Configure the unattended robot to open an **interactive Windows session** — a Service Mode Robot using a robot account with Unattended setup and **Windows credentials** (so it auto-logs-on an interactive session), rather than a headless background run.
  - If the process must stay background, wrap the Office activities in a **Use Foreground** activity, which temporarily moves execution into the foreground.
  - **Do NOT run an Office Repair** — install and registration are healthy when Word opens cleanly interactively.
  - Confirm with an out-of-band A/B re-run: foreground / interactive run succeeds vs the background run faulting.
- **If Word is not installed / not COM-capable** on the robot machine: install a supported Microsoft Word desktop edition (interop-capable) for the robot user.
- **If Office COM registration is broken** (Word errors interactively too): run the **Repair Tool for Microsoft Office** (Studio → Home → Tools → Apps) on the robot machine.

If the failure persists after the process runs foreground in a confirmed interactive session with Word installed and registered, capture a `Verbose` robot log plus the full stack and open a UiPath support case.
