# Rpa Job Killed By Autocancel Trigger — Time-Budget Cancellation

This scenario reproduces a runtime fault caused by **an auto-cancel
trigger force-killing a running job after its configured time budget
was exceeded**. The job ends with:

```
System.Exception: Job stopped with an unexpected exit code: 0x40010004
```

(Windows `DBG_TERMINATE_PROCESS`.)

## What this scenario uncovers

**Root Cause:** Job `LongRunningProcess` (key `c3c0b2c3-...`) was
running normally when the `kill-after-10min` auto-cancel trigger
fired at exactly +600 seconds (the configured time budget). The
trigger calls `Stop` with `strategy=Kill` on jobs that exceed their
budget; this run was on the slow end (still healthy, but past the
trigger threshold). The audit log records the actor as `System` —
no human, no service account — with `eventDetails` referencing the
trigger name and time-budget reason.

This maps to:
`references/products/orchestrator/playbooks/job-stopped-exit-code-0x40010004.md`
(the "Operator Kill from Orchestrator" branch, system-trigger
origin).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | minimal `LongRunningProcess` project — single 5-minute Delay activity |
| `fixtures/mocks/responses/*.json` | synthetic `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The Killing transition timestamp at exactly +600s (matching the
trigger's `timeBudgetSeconds: 600`) is the strongest signal. The
audit event's `actorName: "System"`, `eventDetails.triggerType:
"AutoCancel"`, and `reason: "TimeBudgetExceeded"` confirm the
trigger-initiated kill.

## How this differs from the sibling Kill variants

| Scenario | Actor | Surface signal |
|---|---|---|
| `rpa-job-killed-by-operator-ui` | Human user via Orchestrator UI | `actorEmail` is a real user; `clientInfo.ipAddress` present |
| `rpa-job-killed-by-watchdog-account` | Service account via API | `actorName` is a service account; `clientInfo` absent; `origin: API` |
| **this** — `rpa-job-killed-by-autocancel-trigger` | System-initiated cancellation trigger | `actorName` is `System`; `eventDetails.triggerType: AutoCancel`; Killing at exactly +budgetSeconds |

A correct agent matches the **0x40010004 playbook → Operator Kill
branch** and distinguishes the trigger-initiated cancel from a
human or service-account kill by inspecting `actorName: "System"`
and `eventDetails.triggerType: "AutoCancel"`.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `orchestrator/job-stopped-exit-code-0x40010004`
- Agent ran `uip or jobs history` and observed the
  `Running → Killing → Faulted` transition at +600s
- Agent ran `uip admin audit tenant events --search <job-key>` and
  identified the `actorName: "System"` with trigger details
- Conclusion recommends a fix from the acceptable list (raise time
  budget, scope trigger more narrowly, fix the workflow to fit
  budget, or remove trigger)
