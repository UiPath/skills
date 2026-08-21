# Debug-Session Fault Diagnosis — `debug-fault-777`

## Faulting BPMN Element

**`ScriptTask_ComputeDiscount`**

## Offending Runtime Variable

| Variable | Value |
|---|---|
| `discountRate` | `1.75` |

## Likely Root Cause

The script task evaluated a `discountRate` of **1.75**, which exceeds the
runtime-enforced ceiling of **1.0** (100 %). The incident category is
`ScriptEvaluation`, and the error message is explicit:

> *"computed discountRate exceeds the allowed maximum of 1.0."*

The value `1.75` is almost certainly produced by a miscalculated expression
inside `ScriptTask_ComputeDiscount` — e.g., the script divides a discount
amount by the wrong base, multiplies where it should divide, or uses a raw
percentage (175) instead of a decimal fraction (0.175). With `basePrice = 240`
as the only numeric input visible, a likely candidate is
`discountRate = discountAmount / basePrice` where `discountAmount` was set
to `420` (or similar) by an upstream task, yielding `420 / 240 ≈ 1.75`.

## Safe Next Action

1. **Inspect the script expression** in `ScriptTask_ComputeDiscount` in the
   BPMN source — confirm whether the formula should produce a value in
   `[0.0, 1.0]` (decimal fraction) and fix the arithmetic accordingly.
2. **Check upstream variable assignments** that feed `discountRate` or
   `basePrice` to ensure no prior task is writing an out-of-range value.
3. After fixing the expression, re-validate with the bundled validator and
   re-run the debug session to confirm the corrected value satisfies the
   `≤ 1.0` constraint.

> **No runtime mutations were performed.** Retry, cancel, and cursor-movement
> actions require explicit user consent after the source defect is resolved.
