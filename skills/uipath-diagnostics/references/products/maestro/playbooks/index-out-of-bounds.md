---
confidence: low
---

# Index Outside Bounds of Array (502)

## Context

What this looks like:
- HTTP 502 surfaced by Maestro with `System.IndexOutOfRangeException`
- Error message: `Index was outside the bounds of the array.`
- No actionable detail in `errorDetails` beyond the stack trace

What can cause it:
- Server-side bug — engine accessed an array slot that doesn't exist
- Incorrect Orchestrator URL (trailing slash, wrong tenant path) causing client init to read past expected segments
- Culture data initialization failure on the host
- Re-entry into an already-executed parallel multi-instance subprocess — historical case where a follow-up workflow updated files and tried to re-run prior steps

What to look for:
- Stack trace in `errorDetails` — what component is throwing
- Whether the workflow loops back into a parallel multi-instance subprocess
- Whether the Orchestrator URL in the tenant settings is well-formed

## Investigation

1. Get the incident: `uip maestro instance incidents <instance-id> -f <folder-key> --output json` — preserve the full stack trace
2. Walk element executions: `uip maestro instance element-executions <instance-id> -f <folder-key> --output json` — note the element that faulted
3. Check whether the workflow attempted to re-enter a multi-instance subprocess that already completed
4. If reproducible, gather: Orchestrator URL config, exact `.bpmn`, sample inputs

## Resolution

- **If re-entry into completed multi-instance subprocess:** redesign so the follow-up path uses a fresh subprocess instead of re-entering the original
- **If bad Orchestrator URL:** correct the tenant URL (no trailing slash, correct tenant path)
- **If stack trace points at culture data:** escalate to platform/infra — server-side fix needed
- **If no actionable root cause from the stack trace:** open a UiPath support ticket with the full stack trace, the `.bpmn`, the instance ID, and a minimal repro

## Notes

- This error is **Not Diagnosable** to a user-actionable fix from PIMS API alone — it almost always indicates a platform bug. Capture the stack trace and escalate

## References

- [Docs: Orchestrator Exceptions](https://docs.uipath.com/orchestrator/standalone/2024.10/installation-guide/orchestrator-exceptions)
- [Forum: Index was outside the bounds](https://forum.uipath.com/t/could-not-create-orchestrator-client-exception-index-was-outside-the-bounds-of-the-array/799616)
