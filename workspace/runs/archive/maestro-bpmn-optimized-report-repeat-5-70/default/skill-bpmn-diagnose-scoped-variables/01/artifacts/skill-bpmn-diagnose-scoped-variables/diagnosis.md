# Diagnosis — Instance inst-triage-001 (SubProcess_TaxCalc)

## Diagnostic steps

1. Read process-level variables (`scope: process`) — `invoiceTotal` = `1200.00`,
   `runStatus` = `Completed`. Both look plausible.
2. Read subprocess-scoped variables for `SubProcess_TaxCalc`
   (`--parent-element-id SubProcess_TaxCalc`):

   | Variable | Value |
   |---|---|
   | `taxableBase` | `1200.00` |
   | `taxRate` | `0.00` |
   | `taxAmount` | `0.00` |

   `taxableBase` matches the invoice total correctly. However, `taxRate` is
   `0.00`, so the multiplication `taxableBase × taxRate` produced `taxAmount =
   0.00` — meaning no tax was applied at all.

## Root cause

OFFENDING_VARIABLE: taxRate
OFFENDING_VALUE: 0.00

The subprocess variable `taxRate` was never assigned a real rate (e.g. `0.10`
for 10 %). It was either left at its default zero value or mapped from an
upstream data source that returned zero. Downstream, `taxAmount` is derived
entirely from this rate, so the computed tax on a `$1200.00` invoice became
`$0.00`.

## Why a Completed status does not guarantee correctness

A `Completed` status only proves that all BPMN sequence flows reached their end
event without an unhandled fault — the process engine's job is to move control
from element to element, not to audit the business meaning of the data those
elements produce. Semantic errors (wrong constants, missing upstream data, bad
expressions that happen not to throw) are invisible to the control-flow engine:
the subprocess exits normally, the parent process continues, and the overall
instance reaches `Completed` even though every tax figure it emitted is wrong.
Runtime variables are the only way to verify that the *values* — not just the
*flow* — are correct.
