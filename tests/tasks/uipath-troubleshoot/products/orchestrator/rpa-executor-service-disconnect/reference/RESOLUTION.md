# Resolution — NightlyPost "Job faulted due to service shutdown or disconnect"

## Root Cause

Job `d4a40001-4444-4444-8444-444444444444` (process `NightlyPost`, folder
Batch Ops) ran on BATCH-BOT-02 for ~68 seconds (history Pending → Running →
Faulted) and then faulted with:

```
Job faulted due to service shutdown or disconnect.
```

This is a **transient** event: the Robot service on BATCH-BOT-02 shut down or
lost its connection to Orchestrator while the job was executing, so the run was
marked Faulted. It is not a persistent config, credential, license, slot, or
console problem — the message points at a **service/connection** event, and the
**previous nights' NightlyPost runs on the same host and account succeeded**
(intermittent, not systemic).

Matches `products/orchestrator/playbooks/executor-start-transient-rerun.md`
(rerun-class).

## Fix

- **Rerun the job.** These service-shutdown/disconnect faults are transient; a
  fresh run on a healthy host typically completes (the prior nightly runs
  confirm the automation and credentials are fine).
- **If it recurs on BATCH-BOT-02:** investigate host/robot stability — the
  Robot service restarting (updates, reboots, resource pressure) or dropping
  its Orchestrator connection (network) mid-run — and update the Robot to the
  latest version. A one-off is expected transient noise; a pattern points at
  host maintenance windows overlapping the schedule or an unstable
  robot-to-Orchestrator link.

## Must NOT attribute

Do not attribute this to: a logon/credential failure (there is no `Logon
failed` / `0x000005..` code, and prior runs on the same account succeeded); a
`Creating user session timed out` defect; a `workstation is in use` /
`console` slot/console conflict; a serverless Robot Units / licensing quota; or
a workflow/activity bug (the message is a robot-service event, not an activity
exception). The correct first action is a rerun, escalating to host/robot
stability only if it recurs — not a credential, slot, license, or code change.
