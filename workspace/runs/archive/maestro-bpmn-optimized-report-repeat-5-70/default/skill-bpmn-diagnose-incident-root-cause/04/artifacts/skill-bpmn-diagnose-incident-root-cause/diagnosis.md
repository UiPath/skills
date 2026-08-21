# Instance Failure Diagnosis

**Instance:** inst-triage-001  
**Folder:** folder-public  
**Total incidents:** 2

---

ROOT_CAUSE_ELEMENT: ServiceTask_FetchInvoice
ROOT_CAUSE_CATEGORY: BindingResolution

---

## Why the second incident is downstream noise

The second incident (`inc-noise-002`) was raised against `ServiceTask_PostToLedger`
with category `UpstreamDependencyFailed`. Its `message` explicitly states:
*"Element was cancelled because an upstream element (inc-root-001) never completed."*
Its `causedBy` field points directly to `inc-root-001`, and its `sequence` value
(2) is later than the root fault's sequence (1).

The `incident summary` command corroborates this: `firstFaultElementId` is
`ServiceTask_FetchInvoice` with `BindingResolution` at sequence 1, and the
runtime's own note records that `UpstreamDependencyFailed` incidents are
downstream consequences of the first fault.

In other words, `ServiceTask_PostToLedger` never had a chance to execute — the
runtime cancelled it automatically once `ServiceTask_FetchInvoice` failed to
start. Fixing the binding resolution problem on `ServiceTask_FetchInvoice`
(binding name: `invoiceSource`) will eliminate both incidents; `ServiceTask_PostToLedger`
itself has no independent defect.
