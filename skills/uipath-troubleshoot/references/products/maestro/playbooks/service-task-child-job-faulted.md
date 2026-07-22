---
confidence: high
---

# Service Task Child Job Faulted (170002)

## Context

What this looks like:
- Maestro instance stuck in Running state with an open incident
- Incident error code 170002 — "Failure in the Orchestrator Job"
- Child job launched by a service task has faulted

What can cause it:
- The child RPA job or agent faulted (selector failure, application exception, argument mismatch, etc.)
- The child job was stopped or cancelled externally
- Robot disconnected mid-execution

Ownership: `170002` means "Failure in the Orchestrator Job" - the child job's diagnosis belongs to the Orchestrator playbooks (and the failing activity's package playbooks). This playbook owns the Maestro surface only: the incident, the service task that launched the job, and unblocking the instance.

What to look for:
- The child job's error message and final state — the child's failure reason is the actual root cause, not the parent's error code
- Which service task in the BPMN process triggered the child job
- Whether the service task has a boundary error event attached

## Investigation

Service tasks are a BPMN concept — use the `bpmn` subcommand. For Flow/Case service-equivalent failures, swap `bpmn` for `flow` or `case`.

1. Get full incident details: `uip maestro bpmn instance incidents <instance-id> -f <folder-key> --output json`
2. Get element executions to identify the faulted service task: `uip maestro bpmn instance element-executions <instance-id> -f <folder-key> --output json`
3. Find the child job key from the incident's `errorDetails` and get its state and error message: `uip or jobs get <child-job-key> --output json`
4. Get child job logs for execution detail: `uip or jobs logs <child-job-key> --level Error --output json`
5. Check whether a boundary error event is attached to the service task (visible in element executions)
6. Hand off the child job diagnosis to the owning Orchestrator playbook, routed on the child's state/error:
   - Stuck in Running, no progress → [job-stuck](../../orchestrator/playbooks/job-stuck.md)
   - Pending, "No host is available on the machine template" → [job-pending-no-host](../../orchestrator/playbooks/job-pending-no-host.md) (or [job-pending-stale-dispatch](../../orchestrator/playbooks/job-pending-stale-dispatch.md) per its discriminator)
   - Faulted with `Could not start executor` / logon errors → [job-faulted-logon-failure](../../orchestrator/playbooks/job-faulted-logon-failure.md)
   - Other faults (activity/selector/application errors) → the [Orchestrator summary](../../orchestrator/summary.md) or the failing activity's package playbooks
   - No row matches → extract the child's exception class, error code, and activity namespace from the logs and grep the playbook corpus for those signals to find the owning playbook

## Resolution

- **Resolve the open incident** to unblock the BPMN instance — either retry the service task or mark the incident as resolved, depending on process design
- **Add a boundary error event** to the service task in Studio Web so future child job failures are caught and routed to an error-handling flow (retry, notification, or alternative path) instead of blocking the instance with an unresolved incident
- **Root cause is in the child domain** - the fix comes from the Orchestrator/package playbook reached in Investigation step 6, not from this one
