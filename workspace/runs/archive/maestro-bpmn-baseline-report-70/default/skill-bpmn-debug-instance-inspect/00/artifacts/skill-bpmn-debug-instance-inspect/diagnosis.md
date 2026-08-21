# BPMN Debug-Session Fault Diagnosis

**Debug instance:** `debug-fault-777`

---

## Faulting BPMN Element

| Field | Value |
|---|---|
| Element ID | `ScriptTask_ComputeDiscount` |
| Category | `ScriptEvaluation` |
| Incident ID | `inc-dbg-777` |

---

## Offending Runtime Variable

| Variable | Value |
|---|---|
| `discountRate` | `1.75` |

---

## Likely Root Cause

The script task `ScriptTask_ComputeDiscount` computes a `discountRate` and
enforces a guard that the value must not exceed `1.0` (i.e., 100 %).
At runtime, `discountRate` was evaluated to **1.75**, which violates that
constraint and caused the script to throw, faulting the instance.

The upstream data driving the calculation is `basePrice = 240` (order
`ORD-DBG-777`). The most likely causes are:

1. **Incorrect discount formula** — the script applies a percentage
   expression that produces a ratio > 1 instead of a fraction ≤ 1
   (e.g., multiplying by 175 instead of dividing by 100).
2. **Bad input data** — a discount lookup returned a raw percentage
   value (175) that was not normalised to a decimal fraction before
   being assigned to `discountRate`.

---

## Safe Next Action

Fix the script or the data-normalisation logic in
`ScriptTask_ComputeDiscount` so that `discountRate` is always in the
range `[0.0, 1.0]` before the guard is evaluated, then re-run the debug
session from the beginning to confirm the fault no longer occurs.

> **No operational action was taken on the instance** — this is a
> read-only diagnosis of the debug session.
