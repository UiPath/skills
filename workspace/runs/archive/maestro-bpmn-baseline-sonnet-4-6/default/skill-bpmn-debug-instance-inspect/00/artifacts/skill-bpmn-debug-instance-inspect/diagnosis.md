# BPMN Debug Session Fault Diagnosis

**Debug instance ID:** `debug-fault-777`

---

## Faulting BPMN Element

| Field | Value |
|---|---|
| Element ID | `ScriptTask_ComputeDiscount` |
| Element Type | Script Task |
| Incident Category | `ScriptEvaluation` |

---

## Offending Runtime Variable

| Variable | Value | Allowed Range |
|---|---|---|
| `discountRate` | `1.75` | `0.0 – 1.0` (maximum inclusive) |

Supporting variables present at the time of fault:

- `orderId`: `ORD-DBG-777`
- `basePrice`: `240`

---

## Likely Root Cause

The script inside `ScriptTask_ComputeDiscount` derives `discountRate` from
`basePrice` (and presumably other upstream inputs) using logic that can produce
a value greater than `1.0`. The computed value `1.75` represents a 175%
discount, which violates the element's guard constraint. The engine throws
immediately on evaluation, halting the instance before the task completes.

The most probable causes (in order of likelihood):

1. **Formula error** — a multiplication or division in the discount calculation
   is inverted (e.g. `basePrice / promoFactor` where the operands are
   swapped), producing a rate well above 1.
2. **Missing input clamp / validation** — an upstream variable (e.g. a promo
   multiplier or tier discount from a prior task) arrived in a range the
   script does not guard against, and the script naïvely propagates it.
3. **Wrong data type / unit** — `discountRate` was intended to be a percentage
   integer (e.g. `75`) that should be divided by 100 before use, but the
   division step is absent.

---

## Safe Next Action

**Fix the discount-rate formula in `ScriptTask_ComputeDiscount`** so that the
computed `discountRate` is clamped to `[0.0, 1.0]` before the script exits,
or add upstream validation that rejects / corrects promo inputs that would
produce an out-of-range rate.

Specifically:

1. Open the BPMN definition and locate the script body for
   `ScriptTask_ComputeDiscount`.
2. Identify whether the fault is a formula inversion, a missing ÷100
   conversion, or an unvalidated upstream variable.
3. Apply the fix in the process definition and **re-launch a new debug
   session** to verify that `discountRate` falls within `[0.0, 1.0]` before
   promoting to production.

> **Do not retry, cancel, or continue the faulted debug instance
> `debug-fault-777` directly** — the fix must be applied in the process
> definition first.
