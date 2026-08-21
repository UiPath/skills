# Debug-Session Fault Diagnosis — `debug-fault-777`

## Faulting BPMN Element

| Field | Value |
|---|---|
| Element ID | `ScriptTask_ComputeDiscount` |
| Element type | Script Task |
| Incident category | `ScriptEvaluation` |
| Incident message | *Script task threw: computed discountRate exceeds the allowed maximum of 1.0.* |

## Offending Runtime Variable

| Variable | Value |
|---|---|
| `discountRate` | `1.75` |

The script task computed `discountRate = 1.75`, which exceeds the domain maximum of `1.0` (i.e. 100 %). The guard check inside the script threw immediately, faulting the element.

`basePrice` (`240`) is a plausible input and is not itself the cause.

## Likely Root Cause

The discount-computation formula (or an upstream input) produced a rate greater than `1.0`. The most common causes are:

1. **Formula error** — the script divides or multiplies in the wrong order (e.g. `discountAmount / unitPrice` where `discountAmount > unitPrice`).
2. **Wrong input units** — the caller passed `discountRate` as a percentage integer (e.g. `175` for 175 %) and the script expected a fraction (`0.0–1.0`), so it stored the raw value without normalising.
3. **Missing clamp / validation** — the script has no guard that clamps or rejects values before writing to `discountRate`.

## Safe Next Action

Fix the BPMN source in the Author step:

- Open `ScriptTask_ComputeDiscount` in the `.bpmn` and correct the formula so the result is always in `[0.0, 1.0]`, **or** add an explicit clamp/guard (`Math.min(rate, 1.0)`) and an error path if the raw value is semantically invalid.
- Validate locally (`validator/validate-bpmn.mjs`) after the edit.
- Re-run the debug session with a representative `basePrice` / discount input to confirm `discountRate` stays within bounds before promoting the package.

> **No instance mutation performed.** This is a diagnosis only. Retry, cancel, or continue actions require explicit consent after the source defect is resolved.
