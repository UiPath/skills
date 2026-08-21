# Debug-Session Fault Diagnosis

**Debug instance:** `debug-fault-777`

## Faulting BPMN Element

| Field | Value |
|---|---|
| Element ID | `ScriptTask_ComputeDiscount` |
| Element type | Script Task |
| Incident ID | `inc-dbg-777` |
| Category | `ScriptEvaluation` |

## Offending Runtime Variable

| Variable | Value |
|---|---|
| `discountRate` | `1.75` |

The script task enforces a maximum discount rate of `1.0` (100 %). At runtime
`discountRate` resolved to `1.75`, violating that guard and causing the task to
throw.

## Likely Root Cause

The input value `basePrice = 240` fed into the discount-computation script
produced `discountRate = 1.75` — a value greater than the allowed ceiling of
`1.0`. The most likely causes are:

1. **Calculation error in the script expression** — the discount formula divides
   or multiplies incorrectly (e.g. uses the wrong denominator), yielding a rate
   above 1.0 for this input.
2. **Bad upstream data** — an upstream mapping passed an already-scaled or
   incorrect `basePrice` (or a discount input) that makes the computed ratio
   exceed 1.0.

The fault is in BPMN source: either the script expression inside
`ScriptTask_ComputeDiscount` or the variable mapping that feeds it.

## Safe Next Action

1. **Open `ScriptTask_ComputeDiscount` in the BPMN source** and review the
   discount-rate formula. Verify the expression cannot produce a value > 1.0 for
   any valid `basePrice`.
2. **Add a guard or clamp** (`discountRate = Math.min(computed, 1.0)`) if the
   intent is to cap rather than reject, or fix the formula if the result is
   simply wrong.
3. **Re-validate** with the bundled validator after the source edit, then
   repackage and re-run the debug session.

> **No instance operations were performed.** This is a read-only diagnosis.
> No retry, cancel, continue, or migrate actions were taken.
