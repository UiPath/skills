---
confidence: medium
---

# Screen Capture Failed — Win32 "The handle is invalid" (no interactive desktop)

## Context

A screen-surface activity (Take Screenshot, image-based / Computer Vision capture, `CopyFromScreen`) throws a Win32 exception because there is **no valid interactive desktop to capture** — the unattended session has no live console/RDP surface, or the session was disconnected/locked while the job ran. GDI screen capture needs a real, active desktop; without one, the handle is invalid.

What this looks like:
- `System.ComponentModel.Win32Exception (6): The handle is invalid. at System.Drawing.Graphics.CopyFromScreen(...)`
- Faults at a screenshot / image-capture / screen-scrape step, not at job start
- Happens on unattended runs, disconnected RDP sessions, or locked/minimized sessions — and typically NOT when a human is watching the session live
- Intermittent: works when the session is active/connected, fails when it is not

What can cause it:
- **Unattended robot with no interactive session surface** — `LoginToConsole` is off and no RDP session is established, so there is no desktop to capture
- **RDP session disconnected / logged off** mid-run — the desktop surface went away under the job
- **Session locked / screensaver / minimized** — the desktop is not renderable for capture
- Occasionally a Robot/driver defect (see `known-issue-robot-defect.md` — check version)

## Investigation

1. Get the failing job and read the exception:
   `uip or jobs get <job-key> --output json` — `Info` shows the `Win32Exception (6): The handle is invalid` at `CopyFromScreen`.
2. Find the failing activity in traces:
   `uip or jobs traces <job-key> --output json` — the screenshot / image-capture activity Faulted; prior non-screen activities succeeded.
3. Check the robot user's session configuration:
   `uip or users get <user-key> --output json` — `LoginToConsole` (false ⇒ no console surface unless RDP is established) and whether this is an unattended user expected to have its own session.
4. Check session stability around the failure: whether an RDP session was disconnected/logged off or the host locked at the failure timestamp (job history + host events).

## Resolution

- **Unattended run with no session surface:** give the robot a live interactive session — enable **Login to Console** for the unattended user (Orchestrator → Tenant → Users/Robots → Execution Settings) so the Robot creates its own console session with a real desktop, then rerun.
- **RDP session disconnected/logged off:** keep the session alive — do not log off or "X" out of the RDP window (use Disconnect deliberately, or run via Login to Console). Ensure the session stays connected for the duration of screen-surface work.
- **Session locked / minimized:** prevent lock/screensaver on the robot host during unattended runs; ensure the target window is activated (`Activate`) before capture.
- **Design alternative:** avoid raw full-screen `CopyFromScreen` in headless contexts — prefer element-scoped capture, or capture a specific window/UI element rather than the whole desktop.
- **If it persists on a current session with a live desktop:** check the Robot version against known issues (`known-issue-robot-defect.md`) — a driver/build defect can also surface as an invalid handle.

Prevention:
- For any unattended automation that takes screenshots or uses image-based/CV activities, guarantee a live interactive session (Login to Console) — screen capture cannot run headless.
- Keep RDP sessions connected and unlocked for the duration of screen-surface steps.
