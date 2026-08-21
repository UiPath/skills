# Incident Root-Cause Diagnosis

**Instance:** inst-triage-001  
**Folder:** folder-public  
**Total incidents:** 2

---

ROOT_CAUSE_ELEMENT: ServiceTask_FetchInvoice
ROOT_CAUSE_CATEGORY: BindingResolution

---

## Analysis

### Root fault — `ServiceTask_FetchInvoice` (inc-root-001)

`ServiceTask_FetchInvoice` raised the first incident (sequence 1, occurred at
2026-05-01T12:00:03Z) with category `BindingResolution`. The runtime could not
resolve the resource binding named `invoiceSource`, so the element never
started. This is a self-contained failure: the element faulted before producing
any output, with no dependency on any prior step.

`uip maestro bpmn incident summary` independently confirms this as the
`firstFaultElementId` / `firstFaultCategory` for the run.

### Downstream noise — `ServiceTask_PostToLedger` (inc-noise-002)

`ServiceTask_PostToLedger` raised the second incident (sequence 2, occurred at
2026-05-01T12:00:07Z, four seconds after the root fault) with category
`UpstreamDependencyFailed`. The incident payload explicitly records
`"causedBy": "inc-root-001"` and its message states: *"Element was cancelled
because an upstream element (inc-root-001) never completed."*

This is propagated cancellation, not an independent fault. `ServiceTask_PostToLedger`
depended on the output of `ServiceTask_FetchInvoice`. Because the upstream task
never produced its output (due to the binding resolution failure), the runtime
automatically cancelled the downstream task. Had the binding on
`ServiceTask_FetchInvoice` resolved successfully, `ServiceTask_PostToLedger`
would never have raised an incident at all.

### Conclusion

The single root fault is the unresolved resource binding (`invoiceSource`) on
`ServiceTask_FetchInvoice`. Fixing that binding is the only source change
required; the `UpstreamDependencyFailed` incident on `ServiceTask_PostToLedger`
will disappear automatically once the upstream element can start and complete
normally.
