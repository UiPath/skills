# BPMN Incident Root Cause Diagnosis

**Instance:** inst-triage-001  
**Folder:** folder-public  
**Total incidents:** 2

---

ROOT_CAUSE_ELEMENT: ServiceTask_FetchInvoice
ROOT_CAUSE_CATEGORY: BindingResolution

---

## Why the other incident is downstream noise

The second incident (`inc-noise-002`, element `ServiceTask_PostToLedger`, category
`UpstreamDependencyFailed`) is not an independent fault. Its own message explicitly
states: *"Element was cancelled because an upstream element (inc-root-001) never
completed."* The `causedBy` field links it directly to `inc-root-001`, and it arrived
four seconds later (sequence 2 vs. sequence 1).

`ServiceTask_FetchInvoice` failed first (sequence 1, `occurredAt`
`2026-05-01T12:00:03Z`) because its resource binding named `invoiceSource` could not
be resolved at runtime (`BindingResolution`). The process runtime then propagated a
cancellation signal to every element that was waiting on `ServiceTask_FetchInvoice`'s
output, causing `ServiceTask_PostToLedger` to fault with
`UpstreamDependencyFailed` — a mechanically generated consequence, not an independent
defect.

Fixing the binding resolution failure on `ServiceTask_FetchInvoice` (e.g., by
repairing the `invoiceSource` binding in the BPMN source or correcting the cloud
configuration it references) will eliminate both incidents. The ledger task requires
no independent fix.
