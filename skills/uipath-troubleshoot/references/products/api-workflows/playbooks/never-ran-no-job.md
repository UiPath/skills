---
confidence: medium
---

# Published API Workflow Never Ran — No Job Was Created

## Context

What this looks like:
- The user reports the integration "didn't run", "stopped running", or "ran yesterday but not today" — and there is no failed job to inspect, because **no job record exists** for the expected window
- `uip or jobs list` for the process returns nothing in the window, or its most recent job predates the expected run
- The workflow itself is clean: `uip api-workflow run --no-auth` succeeds, and the last cloud job (if any) was `Successful`

**Discriminator — check this first.** This playbook is for the absence of a job record. If a job exists, you are in a different family:

| Evidence | Go to |
|---|---|
| Job exists, faulted or `Result: "Failure"` | [run-not-successful.md](./run-not-successful.md) |
| Job exists, stuck `Pending` | Orchestrator — `job-pending-no-host.md` / `job-pending-stale-dispatch.md` |
| Job exists, ran ~15 min then stopped | [platform-limits.md](./platform-limits.md) |
| Job rejected at allocation, near-zero runtime | Orchestrator — `serverless-license-quota.md` |

A published API workflow is invoked three ways, all of them standard Orchestrator process triggers. Identify which one the user expects before investigating — they fail for different reasons:

| Invocation family | How it fires | Where it breaks |
|---|---|---|
| **Time (schedule)** | Cron-style Orchestrator trigger | Trigger disabled, cron/timezone wrong, or the trigger points at a different process version or folder than the one that was republished |
| **Event** | An Integration Service connector event (e.g. a Workday or Salesforce record event) | The IS connection behind the event is broken or disabled — no connection, no event, and the failure surfaces on the connection, not on the workflow |
| **API / on-demand** | Started from Orchestrator (**Automations > Processes > Start a job**), or by another product: an Agent calling it as a tool, Maestro's "Start and wait for API workflow" task action, or a `Run Job` activity in another workflow | The caller never called. The fault is upstream, in the caller — not in this workflow |

What to look for:
- Whether a **trigger** exists for the process at all — a workflow published to a personal workspace is runnable but has no trigger unless one was created
- Whether the republished version and the trigger point at the **same process and folder**. The same package can be deployed to several folders; a trigger bound to the old deployment keeps firing the old version, or stops firing entirely if that deployment was removed
- For event triggers, the connection's ping verdict — a disabled connection silently produces no events

## Investigation

1. Confirm no job exists, rather than a job you have not found. Check the process and folder the user means: `uip or processes list --output json`, then `uip or jobs list --output json`. An empty result in the wrong folder is not evidence — re-check the folder before concluding.
2. Identify the invocation family. Ask the user if it is not evident; do not assume a schedule. `uip or processes get <process-key> --output json` confirms the deployed process and its folder.
3. **Time trigger** — list the triggers bound to the process and read their enabled state and schedule: `uip or triggers list --output json`, then `uip or triggers get <trigger-key> --output json`. Then read the firing record: `uip or triggers history --output json`. A trigger with no history entries in the window did not fire; a trigger with history entries but no jobs fired and failed to start — that is a different fault, go to the Orchestrator pending/allocation playbooks.
4. **Event trigger** — ping the connection the event is bound to: `uip is connections ping <connection-uuid> --output json`. `Result: "Failure"` / `not enabled` means the event source is dead; the workflow is not at fault. See [connection-auth-failure.md](./connection-auth-failure.md) for the connection's own states.
5. **API / on-demand** — the caller is the entity to investigate. Follow the chain **one hop** to the caller's own run (the Agent run, the Maestro instance, the parent job) and diagnose there. Per SKILL.md §4, deeper than one hop → escalate.

## Resolution

- **If no trigger exists:** the workflow was published but never scheduled. Create the trigger, or confirm with the user that invocation is meant to be on-demand — in which case nothing is broken and the question is why the caller did not call.
- **If the trigger is disabled:** re-enable it (`uip or triggers update`), and establish who disabled it and when before closing — a disabled trigger is usually a symptom, not the cause.
- **If the trigger points at a stale deployment:** rebind the trigger to the current process/folder. This is the common failure after a republish that created a new deployment instead of updating the existing one.
- **If the cron or timezone is wrong:** correct the schedule. Confirm against `uip or triggers history` that the next fire lands where expected rather than assuming.
- **If an event trigger's connection is broken:** fix the connection first (re-authenticate via `uip is connections edit <uuid>`), then confirm events resume. The workflow needs no change.
- **If the caller never called:** the root cause is in the caller. Present it as the caller's fault with the propagation path named — do not report the API workflow as healthy without saying what did not invoke it.
