---
confidence: medium
---

# Job Stopped — Unexpected Exit Code 0x40010004

## Context

Orchestrator records `System.Exception: Job stopped with an unexpected exit code: 0x40010004`. The executor (`UiPath.Executor.exe`) was killed via `TerminateProcess` — Windows reports `DBG_TERMINATE_PROCESS` (`0x40010004`). The workflow itself did not throw; the Robot service surfaces the missing graceful shutdown as a Faulted job.

What this looks like:
- Job state: Faulted (occasionally Stopped) with `Info` / error message exactly `System.Exception: Job stopped with an unexpected exit code: 0x40010004`
- No workflow stack trace — origin is the Robot service supervising the executor, not user code
- Execution logs cut off mid-activity; no `Job Completed` / `Execution ended` summary line
- Correlates with an Orchestrator audit action (Stop/Kill), a Windows session event (logoff/disconnect), a service restart, or a host-level event (reboot, OOM, AV quarantine)

What can cause it:
- **Operator Kill from Orchestrator** — `--strategy Kill` (or "Stop" → "Kill" in UI) calls `TerminateProcess` and produces this exact code. `SoftStop` does not.
- **Robot service restart** — `Restart-Service UiPath.Robot`, Robot auto-update, or installer upgrade terminated the executor mid-run
- **RDP disconnected instead of signed out** — leaving an active RDP session in "Disconnected" state drops the user environment for unattended Robots; the executor goes with it. Always sign out (log off) on automation hosts; never "X" the RDP window. `LoginToConsole` in Orchestrator must match the host's actual login model.
- **Session ended on the host** — user logged off, GPO idle-disconnect, fast user switching, or a Windows shutdown event invalidated the user session
- **Robot session timeout exceeded** — `UIPATH_SESSION_TIMEOUT` (typically 60 seconds) elapsed during a long-running step. AI / ML inferences and other slow activities are the common offenders — the Robot considers the session stalled and kills the executor.
- **Machine shutdown / restart / power loss** — host went down while executor was running
- **Process killed externally on the host** — Task Manager, `Stop-Process`, parent process tree termination, AV/EDR quarantine of `UiPath.Executor.exe`
- **Out-of-memory kill** — Windows or a job object terminated executor on memory pressure (Application event log has a Windows Error Reporting entry). AI / ML workloads spike memory hard when models load; an undersized VM running both the bot and the model is the common shape.
- **Native crash in an activity** — non-managed crash (UI automation driver, OCR native lib, browser host) tore down executor; WER artifact on host, abrupt termination on Orchestrator
- **Platform recycle** — cloud / serverless robot host was recycled, redeployed, or scaled in mid-run

What to look for:
- `uip or jobs history <key>` showing transition into `Stopping` or `Killing` before `Faulted` → operator stop/kill
- Audit events mentioning the job key with action involving Stop/Kill → names the actor
- Windows System log entries for `UiPath.Robot` service stop/start around `EndTime` → service restart
- Security log Logoff (4634, 4647) or session disconnect (4779) for the executor's user/session → session ended
- Application log Windows Error Reporting entry naming `UiPath.Executor.exe` → native crash or OOM
- A new job started on the same Robot immediately after → retry/trigger preempted prior run

## Investigation

1. Confirm the exit code and capture timing. `uip or jobs get <job-key> --output json`. Record `State`, `StartTime`, `EndTime`, `Info`, `MachineName`, `HostMachineName`, `RobotName`. The error string must be exactly `System.Exception: Job stopped with an unexpected exit code: 0x40010004`. Other exit codes encode different causes — this playbook does not apply.
2. Get state history. `uip or jobs history <job-key> --output json`. If transitions include `Running → Stopping → Faulted` or `Running → Killing → Faulted`, the job was stopped by Orchestrator — go to step 3. If transition is `Running → Faulted` with no Stopping/Killing state, the executor died on the host — go to step 4.
3. Identify the actor. Query the audit service in a tight window around `EndTime`:
   ```bash
   uip admin audit tenant events \
     --from-date <EndTime-2min ISO8601> \
     --to-date <EndTime+1min ISO8601> \
     --search "<job-key>" \
     --output json
   ```
   The matching event's `actorName` / `actorEmail` / `eventSummary` names the user, robot account, or system trigger that issued the stop. Empty result → kill did not originate in Orchestrator; move to step 4.
4. Inspect the host. Resolve `HostMachineName` from step 1. On that host:
   - **Robot execution log** — `%LocalAppData%\UiPath\Logs\Execution.log` for the job's user. Find the last activity logged before the abrupt end (no `Job Completed` / `Execution ended` line). Note the last activity — it is the closest signal to a crashing component if step 4b confirms a native crash.
   - **Application event log** — Windows Error Reporting / .NET Runtime entries near `EndTime`:
     ```powershell
     Get-WinEvent -FilterHashtable @{LogName='Application'; StartTime=<EndTime-5min>; EndTime=<EndTime+1min>} |
       Where-Object { $_.ProviderName -in 'Windows Error Reporting','Application Error','.NET Runtime' -or $_.Message -match 'UiPath\.Executor' }
     ```
     A WER entry naming `UiPath.Executor.exe` confirms native crash or OOM. The faulting module in the entry points at the culprit (e.g., `chrome.dll`, `tessocr.dll`, `clr.dll`).
   - **System event log** — Robot service activity:
     ```powershell
     Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=<EndTime-5min>; EndTime=<EndTime+1min>; ProviderName='Service Control Manager'} |
       Where-Object { $_.Message -match 'UiPath' }
     ```
     `UiPath.Robot` stop/start in this window → service restart killed the executor.
   - **Security event log** — session events for the executor's user:
     ```powershell
     Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4634,4647,4779; StartTime=<EndTime-5min>; EndTime=<EndTime+1min>}
     ```
     Logoff (4634/4647) or session disconnect (4779) on the executor's session in this window is the cause.
   - **AV/EDR quarantine** — vendor-specific. Check Defender via `Get-MpThreatDetection | Where-Object { $_.Resources -match 'UiPath' }`.
5. Check for session-timeout kills on long-running steps. If `EndTime - StartTime` of the **last logged activity** approaches `UIPATH_SESSION_TIMEOUT` (typically 60 seconds) — frequently the case for AI/ML inferences, model loads, long HTTP waits, or batch OCR — the Robot likely killed the executor for an unresponsive session. Confirm:
   - Check the environment variable on the host: `[Environment]::GetEnvironmentVariable('UIPATH_SESSION_TIMEOUT','Machine')` (and `User` scope). If unset, the Robot default applies.
   - In `Execution.log`, the abrupt end follows a single long-running activity with no intermediate log lines.
6. If host evidence is unavailable (cloud robot, serverless, host already recycled):
   - `uip or machines list --output json` — confirm the host is still healthy; redeploys and pool scaling recycle executors mid-run.
   - `uip or jobs list --folder-key <key> --process-name <name> --created-after <EndTime-5min> --output json` — a new job created within seconds of `EndTime` indicates a retry policy or trigger fired immediately. Verify whether retry was triggered by the platform (transient infra) vs. configured retry policy.
7. Cross-check related patterns. If the same host repeatedly produces `0x40010004` followed by an orphan `UiPath.Executor.exe`, see [foreground-already-running.md](./foreground-already-running.md) — session-stability is the upstream issue.

The root cause is **who terminated the process and why** — not the exit code. A confirmed finding must name the actor (Orchestrator user, trigger, service restart, session logoff, OOM, native crash, platform recycle) and the evidence backing it.

## Resolution

- **Operator-initiated Kill (audit names the actor):** confirm intent. If unintended, restrict who holds `Jobs.Edit` on the folder (Orchestrator → Roles). Train operators to use `SoftStop` first (`uip or jobs stop <key> --strategy SoftStop`) so the workflow can exit gracefully; reserve `Kill` for genuinely stuck jobs.
- **Robot service restart (System log shows `UiPath.Robot` stop/start):** if Robot auto-update caused it, schedule updates outside production windows (Orchestrator → Machines → Updates) or pin a Robot version. If an admin restarted the service, coordinate maintenance windows around running jobs.
- **Session logoff / RDP disconnect (Security log 4634/4647/4779):** for unattended runs, enable "Login to Console" on the Robot so it owns its own session — and confirm `LoginToConsole` in Orchestrator matches the host's actual login model (console vs. RDP). The inverted rule from typical interactive guidance: on automation hosts, **sign out, do not disconnect** — a "Disconnected" RDP session drops the user environment and kills any running executor with `0x40010004`. Disable idle-disconnect GPOs on the automation account. Also see related sessions in [foreground-already-running.md](./foreground-already-running.md).
- **Robot session timeout exceeded (last activity approached `UIPATH_SESSION_TIMEOUT`):** raise the timeout for the host that runs slow steps — `setx UIPATH_SESSION_TIMEOUT <seconds> /M` (Machine scope), then restart the Robot service. For AI / ML inferences, size the timeout above the worst-case inference time plus model-load. As a workflow-level fix, split the long step into smaller activities (yields heartbeat log lines that reset the timeout) or move the heavy step to a dedicated process / Maestro stage with its own retry policy.
- **Machine shutdown / restart:** correlate with infrastructure change windows. Move automation hosts off generic patch/reboot rings; set Windows Update Active Hours or maintenance groups. For cloud VMs, exclude automation hosts from scheduled recycle policies.
- **AV/EDR quarantine (vendor detection naming `UiPath.Executor.exe`):** allowlist `UiPath.Executor.exe`, `UiRobot.exe`, the project's `bin` directory, and `%LocalAppData%\UiPath`. Capture the quarantine record as evidence before re-running.
- **OOM kill (WER entry with memory pressure or working-set exceeded):** profile the workflow for large in-memory data (DataTables, byte arrays, screenshots); stream rather than buffer. Raise page file or move to a machine template with more RAM. For coded workflows, check for large-object-heap pressure and GC pinning. **AI / ML workloads:** size the host to fit the bot **plus** the model in memory simultaneously, with headroom for inference batches. Lazy-load models, dispose them when idle, and pin model serving to a separate process if a single VM cannot satisfy both.
- **Native crash (WER entry naming a non-UiPath module — `chrome.dll`, `IEFRAME.dll`, `tessocr.dll`, etc.):** isolate the activity logged immediately before the abrupt end. Update the related activity package; if reproducible, capture a `.dmp` via WER and file a support ticket. The workflow cannot recover from a native crash inside the executor.
- **Platform recycle (cloud / serverless robot, no host evidence available):** enable retry on transient infra failures (Orchestrator → Process → Retry Settings). For long-running workflows, checkpoint state (queue items, storage buckets, Maestro persistence) so re-runs resume rather than restart.
- **External `Stop-Process` / Task Manager kill on host:** treat as Orchestrator Kill — intentional but uncontrolled. Tighten host access (restrict RDP into automation hosts; remove Administrator rights from operators).

Prevention:
- Default to `SoftStop` in operator runbooks; reserve `Kill` for stuck jobs.
- Keep automation hosts out of generic patch/reboot rings; schedule maintenance windows around job activity.
- Allowlist UiPath executables and folders in AV/EDR.
- On automation hosts: sign out, do not disconnect. Disable idle-disconnect GPOs on the automation account. Confirm `LoginToConsole` matches the host's login model.
- Size `UIPATH_SESSION_TIMEOUT` against the slowest expected step (especially AI / ML inferences); size host RAM against the bot **plus** the model.
- Isolate risky steps (native automation, OCR, browser hosts, AI inference) into child workflows / Invoke Process so the parent can detect abrupt exit and react.
- For high-value long runs, add checkpointing so a `0x40010004` failure does not lose all work.

## Reference

- UiPath Docs — Execution Troubleshooting and Robot session configuration. Use the latest version on the UiPath documentation portal; do not rely on links cached here.
