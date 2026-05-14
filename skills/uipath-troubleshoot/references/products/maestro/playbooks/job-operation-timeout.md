---
confidence: medium
---

# Job Operation Timeout (502)

## Context

What this looks like:
- HTTP 502 with error message `Job Operation Timeout`
- Job appears completed in Orchestrator logs but Maestro reports timeout
- Instance stuck several minutes past the underlying job's actual end time

What can cause it:
- A gateway/proxy (Azure Application Gateway, Cloudflare, nginx) times out before Orchestrator returns. Typical with synchronous call mode where the HTTP connection is held until the job completes
- Many concurrent action-center tasks each spawning a job — resource contention pushes individual call latency past the gateway threshold
- Serverless/coded RPA timing out at the serverless layer ("automation cancelled because it reached the time limit") — root cause is on the robot side, not Maestro (tracked in past Slack threads as `MST-6379`)

What to look for:
- Whether the underlying child job is actually `Successful` in Orchestrator while Maestro reports timeout — indicates gateway timeout, not runtime failure
- Whether the same workflow times out on subsequent runs — points at sustained gateway/proxy limits
- Concurrent task volume on the folder

## Investigation

1. Get the incident: `uip maestro instance incidents <instance-id> -f <folder-key> --output json`
2. Pull element executions and capture start/complete times of the timing-out activity: `uip maestro instance element-executions <instance-id> -f <folder-key> --output json`
3. Locate the child Orchestrator job ID from the incident `errorDetails` and check its final state: `uip or jobs get <child-job-key> --output json`
4. If the child job is `Successful` but Maestro 502'd, the gateway timed out before Orchestrator's response landed

## Resolution

- **If using synchronous call mode:** switch to **asynchronous** call mode — Maestro polls the status URI instead of holding a connection
- **If behind a reverse proxy:** increase the request timeout on the backend (Application Gateway / nginx / Cloudflare)
- **If serverless/coded RPA timeout:** check the serverless robot logs, raise the time limit on the coded automation, or split the workflow
- **If many concurrent jobs:** stagger the triggers or add a multi-instance marker with a smaller batch instead of one job per task

## References

- [Docs: Call modes explained](https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/call-modes-explained)
- [Docs: Frequently Encountered Orchestrator Errors](https://docs.uipath.com/orchestrator/docs/frequently-encountered-orchestrator-errors)
