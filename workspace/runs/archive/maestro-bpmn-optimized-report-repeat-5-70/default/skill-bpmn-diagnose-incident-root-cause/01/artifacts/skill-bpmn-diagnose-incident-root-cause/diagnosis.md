ROOT_CAUSE_ELEMENT: ServiceTask_FetchInvoice
ROOT_CAUSE_CATEGORY: BindingResolution

## Diagnosis

### Root fault — `ServiceTask_FetchInvoice` (BindingResolution)

Incident `inc-root-001` fired at sequence 1 (2026-05-01T12:00:03Z).  The element
`ServiceTask_FetchInvoice` could not start because its resource binding
(`invoiceSource`) failed to resolve at runtime.  This is the first and only
self-originated fault in the instance: no upstream element triggered it; it
failed on its own missing/invalid binding configuration.

`uip maestro bpmn incident get inc-root-001` and `incident summary` both confirm
this element as `firstFaultElementId` with the earliest sequence number (1) and
category `BindingResolution`.

### Downstream noise — `ServiceTask_PostToLedger` (UpstreamDependencyFailed)

Incident `inc-noise-002` fired at sequence 2 (2026-05-01T12:00:07Z), four
seconds after the root fault.  Its message explicitly states: *"Element was
cancelled because an upstream element (inc-root-001) never completed."*  The
`causedBy` field references `inc-root-001` directly.

`UpstreamDependencyFailed` is a propagation category: the runtime cancelled
`ServiceTask_PostToLedger` solely because its data-flow or control-flow
predecessor (`ServiceTask_FetchInvoice`) never produced output.  There is no
independent defect in `ServiceTask_PostToLedger`; if the binding on
`ServiceTask_FetchInvoice` is fixed, this downstream cancellation disappears
automatically.  Treating `inc-noise-002` as a root cause would be incorrect and
would lead to investigating an element that has nothing wrong with it.

### Recommended fix area

The fix belongs in **BPMN source / CLI enrichment**: the `invoiceSource` binding
in `ServiceTask_FetchInvoice` needs a valid Integration Service connection ID
and resource enrichment (re-run `uip maestro bpmn registry get` with
`--connection-id` / `--object-name`, regenerate `bindings_v2.json`, and
repackage).  No lifecycle action should be taken until the binding defect is
resolved.
