# Tax Calculation Diagnosis — inst-triage-001

## Findings

### Process-level variables (scope: process)

| Variable | Value |
|---|---|
| runStatus | Completed |
| invoiceTotal | 1200.00 |

These look plausible and were not the source of the error.

### Subprocess-scoped variables (scope: SubProcess_TaxCalc)

| Variable | Value |
|---|---|
| taxRate | 0.00 |
| taxableBase | 1200.00 |
| taxAmount | 0.00 |

`taxRate` entered the subprocess as `0.00`. With a zero rate, the expression
`taxableBase × taxRate` correctly evaluates to `0.00`, so `taxAmount` is also
`0.00` — but that is arithmetically correct for the wrong input, not a
calculation error per se.

## Root cause

OFFENDING_VARIABLE: taxRate
OFFENDING_VALUE: 0.00

The subprocess-scoped variable `taxRate` held `0.00` at runtime. Either it was
never assigned a real tax-rate value before `SubProcess_TaxCalc` executed, or a
mapping expression that was supposed to populate it from an upstream output
resolved to zero (e.g., a missing field, an unevaluated literal string `"0.00"`,
or a null-coalescing default of zero). Because `taxAmount = taxableBase ×
taxRate = 1200.00 × 0.00 = 0.00`, the invoice shipped with no tax applied.

## Why a Completed run can still be semantically wrong

A `Completed` status in UiPath Maestro BPMN only certifies that the process
instance reached a valid BPMN end event without throwing an unhandled exception
or incident — it is a **control-flow verdict, not a value-correctness verdict**.
The runtime engine has no knowledge of what a "correct" tax rate is; it faithfully
executes every expression and mapping with whatever values variables hold at the
time. If an input variable is wrong (zero instead of the applicable rate), every
downstream calculation will produce a wrong-but-exception-free result, the
subprocess completes normally, and the process ends in `Completed`. Semantic
validation — asserting that business values are within expected ranges — must be
modeled explicitly (e.g., a boundary event or a gateway that checks `taxRate > 0`)
or enforced outside the process engine. Relying on status alone to confirm
correctness is therefore insufficient for business-critical computations.
