# Rpa Job Killed By Operator UI — Force-Kill From Orchestrator

This scenario reproduces a runtime fault caused by **a human operator
force-killing a running Orchestrator job via the UI**. The job ends
with:

```
System.Exception: Job stopped with an unexpected exit code: 0x40010004
```

(Windows `DBG_TERMINATE_PROCESS`.)

## What this scenario uncovers

**Root Cause:** Job `LongRunningProcess` (key `a1c0b2c3-...`) was
running normally when an operator clicked **Stop → Kill** in
Orchestrator. The Kill strategy calls `TerminateProcess` on the
executor, which Windows reports as exit code `0x40010004`. The audit
log identifies the actor: `Jane Doe (jane.doe@acme.com)` issued the
stop with strategy `Kill` via the Orchestrator UI.

This maps to:
`references/products/orchestrator/playbooks/job-stopped-exit-code-0x40010004.md`
(the "Operator Kill from Orchestrator" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | minimal `LongRunningProcess` project — single 5-minute Delay activity, just enough to make the job long-running and killable mid-execution |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

> **Note on fixtures.** Like sibling synthetic scenarios, the fixtures
> here were authored from the documented playbook signature rather
> than captured from a real `.investigation/` session. The audit
> event content names a synthetic actor (Jane Doe) — the test grades
> whether the agent surfaces the actor identity, not the specific
> name.

## How this differs from the sibling Kill variants

There are **three** scenarios that all exercise the
`job-stopped-exit-code-0x40010004` playbook's Operator Kill branch,
each with a different actor surfaced in the audit event:

| Scenario | Actor | Surface signal |
|---|---|---|
| **this** — `rpa-job-killed-by-operator-ui` | Human user via Orchestrator UI | `actorEmail` is a real user; `clientInfo.ipAddress` present |
| `rpa-job-killed-by-watchdog-account` | Robot / automation account via API | `actorName` is a service account; `eventSummary` mentions "via API" |
| `rpa-job-killed-by-autocancel-trigger` | System-initiated cancellation trigger | `actorName` is `System`; `eventDetails` references the trigger name and time-budget |

A correct agent matches the **0x40010004 playbook → Operator Kill
branch** and identifies the actor from the audit log. The branch
selection is the same across all three; the differentiator is
**who** the agent names in its conclusion.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `orchestrator/job-stopped-exit-code-0x40010004`
- Agent ran `uip or jobs history` and observed the
  `Running → Stopping → Faulted` transition (operator-initiated)
- Agent ran `uip admin audit tenant events --search <job-key>` and
  named the actor (Jane Doe / jane.doe@acme.com) in the conclusion
- Conclusion recommends a fix from the acceptable list (SoftStop vs
  Kill training, restrict `Jobs.Edit`, or confirm intent)
