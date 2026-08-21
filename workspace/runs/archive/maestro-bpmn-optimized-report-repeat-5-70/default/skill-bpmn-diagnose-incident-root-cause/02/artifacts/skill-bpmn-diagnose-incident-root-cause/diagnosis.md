## Diagnosis — Instance inst-triage-001

ROOT_CAUSE_ELEMENT: ServiceTask_FetchInvoice
ROOT_CAUSE_CATEGORY: BindingResolution

### Why the second incident is downstream noise

The instance raised two incidents in strict sequence order:

| Seq | Incident ID   | Element                  | Category                 | Occurred at          |
|-----|---------------|--------------------------|--------------------------|----------------------|
| 1   | inc-root-001  | ServiceTask_FetchInvoice | BindingResolution        | 2026-05-01T12:00:03Z |
| 2   | inc-noise-002 | ServiceTask_PostToLedger | UpstreamDependencyFailed | 2026-05-01T12:00:07Z |

`ServiceTask_FetchInvoice` (sequence 1) is the true root fault: its resource
binding `invoiceSource` failed to resolve, so the element never started or
produced any output.

`ServiceTask_PostToLedger` (sequence 2) carries an explicit `causedBy:
"inc-root-001"` field and a category of `UpstreamDependencyFailed`. This
category is emitted by the runtime whenever an activity is cancelled because a
predecessor task in the same flow path did not complete. In other words, the
ledger task never had a chance to execute on its own — it was cancelled as a
consequence of the fetch task's failure, not because it contained any defect
of its own. The `incident summary` also confirms this interpretation: it
identifies `ServiceTask_FetchInvoice` as `firstFaultElementId` and notes that
`UpstreamDependencyFailed` incidents are downstream consequences of the first
fault.

**Fix target:** the `BindingResolution` failure on `ServiceTask_FetchInvoice` —
verify that the `invoiceSource` resource binding is correctly populated in
`bindings_v2.json` and that the corresponding Integration Service connection is
healthy. Resolving this single fault will eliminate the downstream cancellation
noise on `ServiceTask_PostToLedger`.
