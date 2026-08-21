# Incident Root-Cause Diagnosis

**Instance:** inst-triage-001  
**Folder:** folder-public  
**Total incidents:** 2

---

ROOT_CAUSE_ELEMENT: ServiceTask_FetchInvoice
ROOT_CAUSE_CATEGORY: BindingResolution

---

## Why the second incident is downstream noise

| # | Incident ID | Element | Category | Sequence | occurred |
|---|---|---|---|---|---|
| 1 | inc-root-001 | `ServiceTask_FetchInvoice` | `BindingResolution` | 1 | 2026-05-01T12:00:03Z |
| 2 | inc-noise-002 | `ServiceTask_PostToLedger` | `UpstreamDependencyFailed` | 2 | 2026-05-01T12:00:07Z |

**`ServiceTask_FetchInvoice` is the true root fault.** It fired at sequence 1
(four seconds before the second incident) with category `BindingResolution`: the
`invoiceSource` resource binding could not be resolved, so the element never
started. This is an autonomous, self-contained failure requiring no prior element
to have faulted.

**`ServiceTask_PostToLedger` is downstream noise.** Its incident message
explicitly states *"Element was cancelled because an upstream element (inc-root-001)
never completed"*, its `causedBy` field points directly at `inc-root-001`, and it
carries the category `UpstreamDependencyFailed` — a category the runtime emits
only as a cascading consequence when a predecessor element does not produce its
expected output. `ServiceTask_PostToLedger` itself had no independent fault; it
was cancelled by the runtime's dependency-propagation logic as a direct result of
`ServiceTask_FetchInvoice` failing. The `incident summary` command confirms this
interpretation: `UpstreamDependencyFailed` incidents are downstream consequences
of the first fault, and `firstFaultElementId` is `ServiceTask_FetchInvoice`.

## Recommended fix area

The binding `invoiceSource` on `ServiceTask_FetchInvoice` needs to be resolved in
the BPMN source (Author capability) or in the Integration Service enrichment step,
depending on whether the binding target is a modeled variable or an unresolved
connector resource reference. Retry or re-run should only happen after that
binding is corrected.
