# Diagnosis: Invoice Tax Computed Incorrectly

## Context

- Instance ID: `inst-triage-001`
- Folder key: `folder-public`
- Reported symptom: stakeholder reports the tax on the invoice came out wrong.
- Run status: `Completed`

## Investigation

**Step 1 — Process-level variables** (`uip maestro bpmn instance variables inst-triage-001 -f folder-public --output json`):

```
runStatus     = Completed
invoiceTotal  = 1200.00
```

These look plausible on their own — nothing here signals a problem.

**Step 2 — Subprocess-scoped variables**, inspected on the parent element that
actually performs the tax calculation
(`uip maestro bpmn instance variables inst-triage-001 -f folder-public --parent-element-id SubProcess_TaxCalc --output json`):

```
taxRate       = 0.00
taxAmount     = 0.00
taxableBase   = 1200.00
```

`taxableBase` correctly reflects the invoice amount (1200.00), but `taxRate`
resolved to `0.00` inside `SubProcess_TaxCalc`. Because `taxAmount` is derived
from `taxableBase * taxRate`, a zero tax rate propagates directly into a zero
tax amount — the invoice was completed with no tax applied at all, which
matches the stakeholder's report of an incorrect tax figure.

## Conclusion

OFFENDING_VARIABLE: taxRate
OFFENDING_VALUE: 0.00

The variable scoped to `SubProcess_TaxCalc` — `taxRate` — resolved to `0.00`
instead of the expected non-zero rate. This zero rate is what drove
`taxAmount` to `0.00` on an invoice with a non-zero `taxableBase` (1200.00),
producing the wrong tax the stakeholder flagged.

## Why "Completed" doesn't guarantee correctness

A `Completed` status only tells you that the process's control flow reached
an end event without faulting — every gateway resolved, every task returned,
no incident was raised. It says nothing about whether the *values* flowing
through that control flow were semantically correct. Here, the subprocess
executed cleanly end-to-end: no exception, no incident, no stalled gateway —
so the run legitimately reports `Completed`. But the tax-rate lookup/calculation
inside `SubProcess_TaxCalc` silently produced `0.00` instead of the correct
rate, and nothing in the control-flow outcome would ever surface that as a
failure. This is why diagnosing a "wrong result" complaint requires reading
runtime variables (especially those scoped to the specific element that
performs the suspect calculation) rather than relying on job/instance status
alone — process-level variables looked fine, and only the subprocess-scoped
values exposed the actual defect.
