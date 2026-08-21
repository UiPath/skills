ROOT_CAUSE_ELEMENT: ServiceTask_FetchInvoice
ROOT_CAUSE_CATEGORY: BindingResolution

## Why the second incident is downstream noise

Incident `inc-noise-002` on `ServiceTask_PostToLedger` carries the category
`UpstreamDependencyFailed` and its `causedBy` field explicitly references
`inc-root-001`. The summary also confirms this: `UpstreamDependencyFailed`
incidents are downstream consequences of the first fault, and `inc-noise-002`
has a later sequence number (2) and timestamp (12:00:07Z vs 12:00:03Z).

`ServiceTask_PostToLedger` never had a chance to execute on its own terms — the
runtime cancelled it solely because `ServiceTask_FetchInvoice` never completed.
The ledger task has no independent defect; it would succeed normally if the
binding on `ServiceTask_FetchInvoice` were resolved. Therefore it is noise, not
a root cause.

The true first fault is `ServiceTask_FetchInvoice`: its `invoiceSource` resource
binding failed to resolve at runtime (category `BindingResolution`, sequence 1),
which prevented the element from starting and cascaded into the cancellation of
every downstream element that depended on its output.
