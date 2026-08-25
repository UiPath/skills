# Rpa Job Killed By Watchdog Account — API Kill From Service Account

This scenario reproduces a runtime fault caused by **a watchdog
automation account force-killing a running Orchestrator job via the
REST API**. The job ends with:

```
System.Exception: Job stopped with an unexpected exit code: 0x40010004
```

(Windows `DBG_TERMINATE_PROCESS`.)

## What this scenario uncovers

**Root Cause:** Job `LongRunningProcess` (key `b2c0b2c3-...`) was
running when an automated watchdog (`watchdog-svc@acme.com`) issued
`POST /jobs/{key}/stop` with `strategy=Kill` via the REST API. The
watchdog rule (`HungJobReaper`) had a 180-second threshold and
flagged the job after it exceeded that threshold during a slow
inference. The audit log identifies the actor as a non-human
service account (no `clientInfo` block — there is no browser
session for an API call).

This maps to:
`references/products/orchestrator/playbooks/job-stopped-exit-code-0x40010004.md`
(the "Operator Kill from Orchestrator" branch, API origin).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | minimal `LongRunningProcess` project — single 5-minute Delay activity |
| `fixtures/mocks/responses/*.json` | synthetic `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The audit event's `actorName` (`watchdog-svc`), absence of
`clientInfo`, `origin: "API"` in `eventDetails`, and the
`watchdogRule` / `watchdogThresholdSeconds` fields together
identify a service-account-driven kill rather than a UI click.

## How this differs from the sibling Kill variants

| Scenario | Actor | Surface signal |
|---|---|---|
| `rpa-job-killed-by-operator-ui` | Human user via Orchestrator UI | `actorEmail` is a real user; `clientInfo.ipAddress` present |
| **this** — `rpa-job-killed-by-watchdog-account` | Service account via API | `actorName` is non-human (`watchdog-svc`); `clientInfo` absent; `eventDetails.origin=API` |
| `rpa-job-killed-by-autocancel-trigger` | System-initiated cancellation trigger | `actorName` is `System`; `eventDetails` references trigger name and time budget |

A correct agent matches the **0x40010004 playbook → Operator Kill
branch** and recognizes that the actor is **not a human** by
inspecting the audit fields (no `clientInfo`, non-human
`actorName`, `origin: "API"`).

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `orchestrator/job-stopped-exit-code-0x40010004`
- Agent ran `uip or jobs history` and observed the
  `Running → Killing → Faulted` transition
- Agent ran `uip admin audit tenant events --search <job-key>` and
  identified the actor as a service account (named `watchdog-svc`
  or equivalent), recognizing API origin and absence of `clientInfo`
- Conclusion recommends a fix from the acceptable list (review the
  watchdog rule threshold, restrict watchdog API credentials, or
  accept the kill if it was legitimate)
