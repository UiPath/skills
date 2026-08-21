# Diagnosis: inst-triage-001 — Wrong Tax on Invoice

## Commands Run (diagnostic priority ladder)

```bash
# Step 3 — Process-level variables (plausible, no anomaly)
uip maestro bpmn instance variables inst-triage-001 -f folder-public --output json

# Step 3 — Subprocess-scoped variables for SubProcess_TaxCalc
uip maestro bpmn instance variables inst-triage-001 -f folder-public \
  --parent-element-id SubProcess_TaxCalc --output json

# Step 4 — Deployed BPMN asset (attempted; mock not wired for asset read)
uip maestro bpmn instance asset inst-triage-001 -f folder-public --output json
```

## Findings

### Process-level variables (scope: process)
| Variable      | Value    | Assessment |
|---------------|----------|------------|
| runStatus     | Completed | Control-flow finished normally |
| invoiceTotal  | 1200.00  | Plausible |

### Subprocess-scoped variables (scope: subprocess, parentElementId: SubProcess_TaxCalc)
| Variable     | Value   | Assessment |
|--------------|---------|------------|
| taxableBase  | 1200.00 | Correct — matches invoiceTotal |
| **taxRate**  | **0.00**| **WRONG — zero rate produces zero tax** |
| taxAmount    | 0.00    | Derived symptom: taxableBase × taxRate = 0 |

## Conclusion

OFFENDING_VARIABLE: taxRate
OFFENDING_VALUE: 0.00

The subprocess `SubProcess_TaxCalc` received a `taxRate` of `0.00` at runtime.
With a zero tax rate the multiplication `taxableBase × taxRate` evaluates to
`0.00`, so `taxAmount` is also `0.00` — zero tax appears on the invoice even
though `invoiceTotal` is `1200.00`.

The process-level variables looked plausible and gave no indication of trouble,
which is why the scoped read on `SubProcess_TaxCalc` was necessary.

## Why a Completed run can still be semantically wrong

A `Completed` status only proves that every token in the BPMN process reached
an end event and that control-flow finished without an unhandled fault. The
runtime has no way to know whether the *values* produced along the way are
business-correct. A `taxRate` of `0.00` is a perfectly valid floating-point
number; it causes no exception, no incident, and no gateway to stall — the
subprocess computes a result (zero), writes it back, and exits normally.
Semantic errors like a misconfigured rate, a wrong variable binding, or a
missing upstream lookup are invisible to the execution engine. This is why
behavioral anomalies reported by stakeholders (e.g., "tax is wrong on the
invoice") require a manual variable inspection even on runs whose final status
is `Completed`, because completion only confirms *that* the process ran, not
*what* it computed.
