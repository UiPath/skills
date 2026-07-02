---
confidence: medium
signatures:
  - kind: exception
    value: "System.NullReferenceException"
    note: "on or just after a connector activity — stack shows a ForEach over an IntegrationService SWEntities output; for user-code NREs see null-reference-exception.md"
  - kind: message
    value: "IntegrationService.Activities.SWEntities"
    note: "stack fragment — ForEach enumerating a null connector List/Get output"
---

# Connector Activity — NullReferenceException

## Context

What this looks like — robot exception `System.NullReferenceException` on or just after a connector activity. There is no error code and no message detail; the stack frame is the only signal. In the telemetry it most often surfaces while **enumerating a connector output that is null** — the stack shows `UiPath.Core.Activities.ForEach`1[[...IntegrationService.Activities.SWEntities.<Cxxx>_<operation>_List...]]`, i.e. a `For Each` over a connector "List records" / query output that returned null instead of an empty list.

Which activities produce this:
- **ConnectorActivity** — and the `For Each` / downstream activity that consumes its output.

What can cause it:
- The connector operation returned **no body / null** (not an empty collection), and the workflow iterates or dereferences it without a null guard.
- An **unmapped output argument** — the activity's result was never assigned to the variable the next activity reads.
- A required **input object was null**, so the connector returned nothing and the workflow then dereferenced the missing output.
- The `SWEntities` bundle type changed between publishes (regenerated connector entity), leaving a stale binding that resolves null. (If the exception is instead `InvalidCastException: Unable to cast ... SWEntities ...`, that is a distinct entity-type-mismatch failure, not this playbook.)

## Investigation

NRE is opaque — the goal is to find **which reference was null** and why.

1. **Read the stack frame** from the job log to identify the activity and the consumed type (the `SWEntities.*_List` / `*_Get` type names the operation).
2. If source is available, inspect the connector activity's **output mapping** and the consumer (`For Each` / `Assign`): confirm the output variable is assigned and that the consumer handles an empty/absent result.
3. Determine whether the operation **legitimately returns nothing** for the given input (e.g. a query with no matches) — if so, the defect is the missing null/empty guard, not the connector.
4. Check whether the project was **republished after the connector entity changed** — a stale output binding can resolve null.

## Resolution

- **If the operation can return no rows:** guard the output before use — check for null / empty before the `For Each` or dereference.
- **If the output is unmapped:** assign the connector activity's result to the variable the downstream activity reads.
- **If a required input was null:** populate it (or guard upstream) so the operation returns a result.
- **If a stale binding after republish:** re-bind the connector activity's output to the current entity type and republish.

If none of the above reproduces a null, treat as a low-confidence lead and gather more evidence (full stack, the exact activity, the input/output variables) before concluding.
