# Diagnosis — Invoice Tax Calculation Error

## Instance
- **Instance ID:** inst-triage-001
- **Folder:** folder-public
- **Final status:** Completed

## Investigation

### Process-level variables (scope: process)

| Variable | Value |
|---|---|
| `runStatus` | `"Completed"` |
| `invoiceTotal` | `"1200.00"` |

Process-level variables are plausible and do not explain the wrong tax.

### Subprocess-scoped variables (scope: subprocess, parentElementId: SubProcess_TaxCalc)

| Variable | Value |
|---|---|
| `taxableBase` | `"1200.00"` |
| `taxRate` | `"0.00"` |
| `taxAmount` | `"0.00"` |

The `taxableBase` is correctly set to the invoice total. However, `taxRate` resolved to `0.00` inside the subprocess, which caused the computed `taxAmount` to also be `0.00` — zero tax on a $1,200 invoice.

## Root cause

OFFENDING_VARIABLE: taxRate
OFFENDING_VALUE: 0.00

The variable `taxRate` is scoped to `SubProcess_TaxCalc` and was either initialized to `0.00` without being overwritten by the lookup or calculation logic inside the subprocess, or its input mapping from the process-level context failed silently and left it at its default zero value. Either way, every multiplication downstream (`taxAmount = taxableBase × taxRate`) produced zero, yielding incorrect (missing) tax on the invoice.

## Why a Completed status does not guarantee correctness

A BPMN engine marks a run `Completed` when control-flow reaches a terminating end event without an unhandled fault — it is purely a statement about execution paths, not about the semantic validity of the values those paths produced. A subprocess that multiplies a zero rate by the taxable base will finish normally and advance the token to the end event; the runtime has no knowledge that the tax rate *should* have been non-zero. Semantic correctness requires either output-validation guards inside the model (e.g., a gateway that faults when `taxAmount == 0` for a non-zero base), explicit assertions, or post-run data checks. Without those, a `Completed` status is necessary but not sufficient evidence that the business logic produced a correct result.
