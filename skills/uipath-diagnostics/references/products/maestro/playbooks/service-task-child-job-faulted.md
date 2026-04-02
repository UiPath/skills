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

What to look for:
- The child job's error message and final state — the child's failure reason is the actual root cause, not the parent's error code
- Which service task in the BPMN process triggered the child job
- Whether the service task has a boundary error event attached

## Investigation

1. Get full incident details via `uip maestro instances incidents <instance-id>`
2. Identify the faulted service task from element executions
3. Find and inspect the child job — its error message drives the root cause investigation
4. Check whether a boundary error event is attached to the service task

## Resolution

- **Resolve the open incident** to unblock the BPMN instance — either retry the service task or mark the incident as resolved, depending on process design
- **Add a boundary error event** to the service task in Studio Web so future child job failures are caught and routed to an error-handling flow (retry, notification, or alternative path) instead of blocking the instance with an unresolved incident
- **Root cause is in the child domain** — investigate the child job failure separately (selector issue, permission error, etc.)
