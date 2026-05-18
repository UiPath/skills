---
confidence: medium
---

# Foreground Process Already Running — InvalidOperationException

## Context

A job fails to start (or terminates immediately) because the Robot refuses to run two foreground (UI-interactive) processes at the same time on the same Windows session. Only one foreground job per session is permitted; additional background jobs may run in parallel.

What this looks like:
- Error message: `System.InvalidOperationException: A foreground process is already running. Only one foreground process can run at a time.`
- Job state: Faulted with near-zero runtime, or never transitions from Pending → Running on the target machine
- Visible in UiPath Robot logs (`%LocalAppData%\UiPath\Logs\Execution.log`) and surfaced in Orchestrator job details
- May appear in Assistant when manually starting a process

What can cause it:
- **Attended Robot conflict** — user starts two processes simultaneously via UiPath Assistant
- **Foreground vs. background misconfiguration** — a non-UI process is built/published as foreground when it doesn't need UI interaction, so it competes for the foreground slot unnecessarily
- **Orchestrator queue overload** — multiple foreground jobs triggered for the same user/Robot at the same time
- Two foreground triggers fire on overlapping schedules against the same Robot/session
- Manual start (Assistant or Orchestrator "Start Job") while a previously scheduled foreground job is still running
- Orchestrator retry policy launches a new attempt before the previous one has fully exited
- **Remote machine session disconnected or minimized** — RDP session was disconnected without logoff; foreground state on the host is inconsistent and the slot appears taken
- Orphaned `UiPath.Executor.exe` or `UiRobot.exe` from a prior run still holds the foreground slot (often after an abnormal session termination — see related `STATUS_CONTROL_C_EXIT` / RDP-drop scenarios)
- Concurrent attended + unattended execution on the same logged-in user session

What to look for:
- Recent job history on the same machine — was another foreground job Running or only recently Completed/Faulted?
- `Process.IsForeground = true` on both the running and the failing process definitions
- A stuck `UiPath.Executor.exe` in Task Manager after the prior job's StartTime, with no corresponding running job in Orchestrator
- Trigger schedules that fire close together (e.g., every 5 min on a 7-min process)

## Investigation

1. Get the failing job: `uip or jobs get <job-key> --output json`. Note `MachineName`, `StartTime`, `EndTime`, and `RobotName`.
2. List recent jobs on the same machine to find an overlapping foreground job:
   `uip or jobs list --folder-path '<folder>' --top 20 --output json`. Look for any Running job, or a Completed/Faulted job whose `EndTime` is at or after the failing job's `StartTime`.
3. Confirm both processes are foreground:
   - Orchestrator UI → Processes → select process → Settings → check "Background Process" is **off** (or `requiresUserInteraction: true`).
4. Check for orphaned executor processes on the host:
   - `Get-Process UiPath.Executor, UiRobot -ErrorAction SilentlyContinue | Format-Table Id, ProcessName, StartTime, SessionId`
   - Cross-reference SessionId with the user that should own the job. An executor running with no matching Orchestrator job is orphaned.
5. Review Robot logs near the failure timestamp: `%LocalAppData%\UiPath\Logs\Execution.log` for prior session terminations (RDP disconnect, session logoff, `0x40010004` exits) that could have left the slot locked.
6. Review trigger configuration: Orchestrator → Triggers — look for cron expressions that can overlap given the typical job duration.

## Resolution

- **Attended Robot conflict (two processes started from Assistant):** stop one of the running processes from the Assistant, then re-trigger sequentially. Educate users that the Assistant cannot run two foreground processes concurrently.
- **Process does not actually need UI interaction:** convert it to a background process at the **source** (Studio → Project Settings → set `"Starts in Background"` to **Yes** in `project.json`, then republish), or at the deployment level (Orchestrator → Process → Settings → "Background Process" = true). Background jobs do not consume the foreground slot.
- **Legitimate concurrent foreground jobs needed:** sequence the triggers so they cannot overlap (stagger cron expressions, chain via Maestro/parent process), or enable **"Run only one job at a time"** on the Robot in Orchestrator (Tenant → Robots → edit → Execution Settings) so subsequent jobs queue instead of failing.
- **Orchestrator queue overload:** for the same user, configure jobs to run sequentially or split the load across multiple Robots/machine templates.
- **Orphaned `UiPath.Executor.exe` / `UiRobot.exe` holding the slot:**
  - Verify it is not bound to an active Orchestrator job before killing.
  - `Stop-Process -Id <pid> -Force` for the orphan, or restart the Robot service: `Restart-Service UiPath.Robot` (run as admin).
  - Investigate **why** it was orphaned (session was killed externally — RDP drop, logoff, machine restart). Repeated orphaning points at session-stability issues, not at this exception.
- **Remote machine session disconnected or minimized:** keep the RDP session alive (do not "X" out — use Disconnect carefully or keep the session active via a console session / kiosk lock), and use `Activate` activities in the workflow so the target window is brought to the foreground reliably. For unattended scenarios, configure "Login to Console" so the Robot can manage its own console session instead of relying on an interactive RDP.
- **Orchestrator retry policy firing too aggressively:** increase the retry delay on the process, or set max retries to 0 and handle failures via a parent workflow that waits for clean state.
- **Attended + unattended collide on the same user session:** isolate attended runs to the user's interactive workflow only and route unattended runs to a separate Robot/machine template.

Prevention:
- Keep at most one foreground process scheduled per Robot session, or enable "Run only one job at a time" on the Robot.
- Default new automations to background (`"Starts in Background": true` in `project.json`) unless they truly require UI interaction.
- For high-throughput scenarios, use multiple Robots or convert UI-less steps to background processes.
- Ensure session terminations clean up — see related session-stability investigation when the orphan pattern repeats.
