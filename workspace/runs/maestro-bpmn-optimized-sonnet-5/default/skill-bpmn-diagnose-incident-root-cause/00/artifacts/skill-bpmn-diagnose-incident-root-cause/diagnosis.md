# Incident Diagnosis — inst-triage-001 (folder-public)

ROOT_CAUSE_ELEMENT: ServiceTask_FetchInvoice
ROOT_CAUSE_CATEGORY: BindingResolution

## Evidence

- `uip maestro bpmn instance incidents inst-triage-001 -f folder-public --output json`
  returned two incidents:
  - `inc-root-001` — sequence 1, element `ServiceTask_FetchInvoice`, category
    `BindingResolution`: "Resource binding failed to resolve; the element could
    not start."
  - `inc-noise-002` — sequence 2, element `ServiceTask_PostToLedger`, category
    `UpstreamDependencyFailed`, with `causedBy: inc-root-001`: "Element was
    cancelled because an upstream element (inc-root-001) never completed."
- `uip maestro bpmn incident get inc-root-001 --folder-key folder-public --output json`
  confirms the fault: a binding named `invoiceSource` failed to resolve at
  `ServiceTask_FetchInvoice`, so the element never started.
- `uip maestro bpmn incident summary --output json` confirms ordering:
  `firstFaultElementId: ServiceTask_FetchInvoice`, `firstFaultCategory:
  BindingResolution`, and explicitly notes "UpstreamDependencyFailed incidents
  are downstream consequences of the first fault."

## Conclusion

`ServiceTask_FetchInvoice` is the true root cause: its resource binding
(`invoiceSource`) failed to resolve, so the task could never start. The second
incident, on `ServiceTask_PostToLedger`, is downstream noise — it is explicitly
tagged `causedBy: inc-root-001` and categorized `UpstreamDependencyFailed`,
meaning the ledger-posting task was only cancelled because the upstream fetch
task it depends on never completed. It occurred four seconds later (sequence 2
vs. sequence 1) and carries no independent fault signal of its own; fixing the
binding at `ServiceTask_FetchInvoice` is the correct and sufficient remediation
target — `ServiceTask_PostToLedger` requires no separate fix.
