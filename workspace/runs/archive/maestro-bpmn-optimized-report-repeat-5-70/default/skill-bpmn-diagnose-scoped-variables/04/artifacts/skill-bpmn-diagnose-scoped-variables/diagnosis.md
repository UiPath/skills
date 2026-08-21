# Diagnosis — inst-triage-001 (SubProcess_TaxCalc)

## Findings

### Process-level variables (scope: process)

| Variable | Value |
|---|---|
| runStatus | Completed |
| invoiceTotal | 1200.00 |

Process-level variables look plausible; the run reached a terminal state and the invoice total is well-formed.

### Subprocess-scoped variables (scope: subprocess, parentElementId: SubProcess_TaxCalc)

| Variable | Value | Assessment |
|---|---|---|
| taxableBase | 1200.00 | correct — matches invoiceTotal |
| taxRate | 0.00 | **WRONG** — rate was never set; should be a non-zero value |
| taxAmount | 0.00 | downstream consequence of taxRate = 0.00 |

## Root cause

`taxRate` was never assigned a non-zero value inside `SubProcess_TaxCalc`. Because `taxAmount` is computed as `taxableBase × taxRate`, a zero rate produces a zero tax regardless of how large the invoice is. The defect is scoped entirely within the subprocess — it is invisible at the process level because `invoiceTotal` is not recalculated from tax components there.

OFFENDING_VARIABLE: taxRate
OFFENDING_VALUE: 0.00

## Why a Completed status does not guarantee semantic correctness

A `Completed` status only proves that control flow reached the end event without an unhandled fault or incident. The BPMN runtime tracks token movement, not business logic invariants. A subprocess can execute all of its activities, produce outputs, and transfer its token to the parent process successfully even if every computed value is wrong. In this case, `SubProcess_TaxCalc` finished executing — it mapped `taxRate` and multiplied it by `taxableBase` without error — but because `taxRate` held its default zero value, the arithmetic was silently incorrect. No exception was raised, no incident was opened, and the process moved to `Completed`. Semantic correctness (whether the right tax was charged) is a business-layer concern that the orchestration engine cannot validate automatically; only an explicit data assertion or a post-process reconciliation step would have surfaced this at runtime.
