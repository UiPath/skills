---
confidence: medium
---

# Could Not Start Executor — Creating User Session Timed Out

## Context

An unattended job faults shortly after entering Running because the Robot could not create a Windows session on the target machine within its session-creation timeout. Unlike a logon *rejection*, nothing refused the credential — the session-creation step **hung and timed out**.

What this looks like:
- Job state: Faulted. Duration ≈ the Robot's session-creation timeout (tens of seconds up to ~2 min) — NOT sub-second like a logon rejection.
- Error `Info` / robot log contains: `Could not start executor. Creating user session timed out.`
- Crucially, there is **NO** Windows logon-failure/locked/RDP-refused signature: no `Logon failed for user`, no `account is locked`, no `RDP connection failed`, no `0x0000052E` / `0x00000775` / `0x00000532` / `Last error: 131092`. A pure timeout, not an LSA verdict.
- Often intermittent — a re-run of the same job on the same machine may succeed.

What can cause it — session creation legitimately took longer than the timeout window. Common drivers:

1. **Slow interactive Windows logon on the host** — a heavy roaming/mandatory profile, synchronous GPO processing, logon scripts, or real-time AV scanning delays session creation past the timeout. Interactive logon on the host is observably slow for humans too.
2. **Host resource exhaustion** — CPU/RAM/session saturation on the target machine prevents timely session creation; host metrics show saturation around the fault time.
3. **Infrastructure / network latency** — slow domain-controller reachability, profile-share latency, or general network/server performance between the Robot and the resources session creation needs.

> **Not a Robot-version defect.** There is no documented Robot version that "fixes" this error and no version below which it is inherent — the UiPath KB attributes it to host resources, Robot/Orchestrator configuration, and infrastructure latency, and it is reported across current Robot versions. Do NOT diagnose it as "upgrade the Robot to version X." Check the Robot version only as general hygiene, never as the cause.

What to look for:
- Exact `Info` / robot-log wording — `Creating user session timed out` with NO logon-failed/locked/RDP-failed code (this is what separates it from `job-faulted-logon-failure.md`).
- Job entered **Running** and then Faulted after ~the timeout window (separates it from Pending / no-host).
- Host health — CPU/RAM/session pressure at the fault time, and whether interactive logon on the host is slow for humans too.
- Whether the failure is intermittent (a retry sometimes succeeds) — consistent with a host/latency margin problem, not a hard fault.

## Investigation

1. **Get the faulted job** — `uip or jobs get <job-key> --output json`. Capture `State`, `Info`, `StartTime`, `EndTime` (duration ≈ session-creation timeout), `HostMachineName`, `RuntimeType`. Confirm `Info` contains `Could not start executor. Creating user session timed out.` and carries **no** logon-failure code.
2. **Get error logs** — `uip or jobs logs <job-key> --level Error --output json`. Confirm the robot-service entry attributes the fault to a session-creation timeout, not an LSA logon rejection.
3. **Confirm it entered Running** — `uip or jobs history <job-key> --output json`. A Pending → Running → Faulted transition rules out the no-host / stuck-Pending playbooks (the job was dispatched and started; session creation is what timed out).
4. **Assess host health and logon latency** — the root sub-cause lives on the host, outside the `uip` surface. Establish from the host/customer: CPU/RAM/session saturation around the fault time, whether interactive logon for a human on that host is abnormally slow (heavy profile / GPO / logon scripts / AV), and any network / DC / profile-share latency. Correlate `HostMachineName` with `uip or machines list --output json` only to identify the host and confirm the Robot is on a supported version (hygiene) — the version is **not** the cause.
5. **(Optional) Corroborate the remediation** — `uip docsai ask "Could not start executor Creating user session timed out UIPATH_SESSION_TIMEOUT" --source technical_solution_articles`. Confirms the documented `UIPATH_SESSION_TIMEOUT` workaround and the host-side causes. An empty KB result is not disconfirming.

## Resolution

Two parts: give session creation enough time, and remove the host-side latency that pushed it past the limit.

- **Raise the session-creation timeout — set the `UIPATH_SESSION_TIMEOUT` environment variable** on the Robot host to a higher value in seconds (the documented workaround; e.g. `300`–`500`), so a legitimately slow session creation completes instead of being cut off. This is the direct remediation for the timeout itself.
- **Reduce interactive-logon latency on the host** — trim the roaming/mandatory profile, make GPO/logon-script processing lighter or asynchronous, and exclude the Robot working directories from synchronous AV scanning.
- **Relieve host resource pressure** — reduce concurrent slots, add CPU/RAM/capacity, or move the workload so the session can be created within the window; use the `Kill Processes` activity to close leftover apps that accumulate and saturate the host.
- **Address infrastructure latency** — check domain-controller reachability, profile-share performance, and network health between the Robot and the resources session creation needs.
- **Interim:** a re-run sometimes succeeds when the host is momentarily less loaded — a stopgap only; raising `UIPATH_SESSION_TIMEOUT` and relieving the host is the durable fix.
- Do **not** treat this as a Robot-version defect — upgrading the Robot is not the documented fix and will not resolve a host-latency / resource cause.

Source: UiPath KB — "How To Troubleshoot The Error 'Could Not Start Executor. Creating User Session Timed Out'" (host resources / Robot-Orchestrator configuration / infrastructure latency; `UIPATH_SESSION_TIMEOUT` workaround, `Kill Processes`, RDS session-limit GPO).
