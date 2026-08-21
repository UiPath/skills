# Debug-Session Fault Diagnosis — `debug-fault-777`

## Faulting BPMN element

`ScriptTask_ComputeDiscount`

## Offending runtime variable

| Variable | Value |
|---|---|
| `discountRate` | `1.75` |

## Likely root cause

The script task that computes the discount rate produced the value `1.75`, which
exceeds the enforced maximum of `1.0` (i.e., 100 %). The script evaluation
guard throws immediately on that condition, faulting the element with incident
category `ScriptEvaluation`. The base input (`basePrice = 240` for order
`ORD-DBG-777`) fed an expression whose output overflowed the valid range —
likely a missing divisor, a percentage/decimal unit mismatch, or an off-by-100
error in the rate formula.

## Safe next action

Fix the discount-rate formula in the `ScriptTask_ComputeDiscount` script so it
always produces a value in `[0.0, 1.0]`. Validate the corrected `.bpmn` locally
with the bundled validator (`validator/validate-bpmn.mjs`) before re-packaging
and re-running. Do not retry the faulted debug instance — the root cause is a
source defect, not a transient runtime error.
