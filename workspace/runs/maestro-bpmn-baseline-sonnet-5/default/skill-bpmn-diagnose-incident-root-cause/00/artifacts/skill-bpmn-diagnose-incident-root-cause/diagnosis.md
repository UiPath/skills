# Incident Root Cause Diagnosis — inst-triage-001 (folder-public)

## Evidence gathered

1. `uip maestro bpmn instance incidents inst-triage-001 -f folder-public --output json`
   returned two incidents:
   - `inc-root-001` — element `ServiceTask_FetchInvoice`, category `BindingResolution`,
     sequence `1`, occurred `2026-05-01T12:00:03Z` — "Resource binding failed to
     resolve; the element could not start."
   - `inc-noise-002` — element `ServiceTask_PostToLedger`, category
     `UpstreamDependencyFailed`, sequence `2`, occurred `2026-05-01T12:00:07Z`,
     `causedBy: inc-root-001` — "Element was cancelled because an upstream
     element (inc-root-001) never completed."

2. `uip maestro bpmn incident get inc-root-001 --folder-key folder-public --output json`
   confirmed the fault detail: a binding named `invoiceSource` failed to resolve
   for `ServiceTask_FetchInvoice`, preventing that element from ever starting.

3. `uip maestro bpmn incident summary --output json` confirmed ordering:
   `firstFaultElementId: ServiceTask_FetchInvoice`, `firstFaultCategory:
   BindingResolution`, with the explicit note: "UpstreamDependencyFailed
   incidents are downstream consequences of the first fault."

## Conclusion

ROOT_CAUSE_ELEMENT: ServiceTask_FetchInvoice
ROOT_CAUSE_CATEGORY: BindingResolution

## Why the other incident is downstream noise

`inc-noise-002` (category `UpstreamDependencyFailed`, element
`ServiceTask_PostToLedger`) is not an independent fault. Its own message states
the element was cancelled solely because an upstream element tied to
`inc-root-001` never completed, and the incident record explicitly sets
`causedBy: inc-root-001`. Its `occurredAt` timestamp (12:00:07Z) is four seconds
after the root fault (12:00:03Z) and its `sequence` value (2) is later than the
root's (1), confirming it fired in reaction to the earlier failure rather than
on its own. The `incident summary` output corroborates this directly, labeling
`UpstreamDependencyFailed` as a downstream consequence of the first fault.
`ServiceTask_PostToLedger` never even attempted to run its own logic — it was
cancelled in place because `ServiceTask_FetchInvoice` could not resolve its
`invoiceSource` binding and never started. Fixing the binding resolution on
`ServiceTask_FetchInvoice` is therefore the only actionable root-cause fix;
`inc-noise-002` will resolve automatically once the upstream element can
complete.
