# Debug-Session Fault Diagnosis

**Debug instance:** `debug-fault-777`

## Faulting BPMN Element

| Field | Value |
|---|---|
| Element ID | `ScriptTask_ComputeDiscount` |
| Incident ID | `inc-dbg-777` |
| Category | `ScriptEvaluation` |

## Offending Runtime Variable

| Variable | Value |
|---|---|
| `discountRate` | `1.75` |

## Likely Root Cause

The script inside `ScriptTask_ComputeDiscount` computed a `discountRate` of **1.75**, which exceeds the enforced maximum of **1.0** (i.e., 100 %). The guard inside the script task throws when the rate is out of range, terminating the debug session with a `ScriptEvaluation` fault.

The upstream cause is almost certainly in the discount calculation logic itself: `basePrice` is **240**, and the expression that derives `discountRate` from it is producing a value greater than 1.0. This is a BPMN source defect — either the formula is wrong (e.g., divides by a constant that is too small) or the input `basePrice` is unexpectedly large for the assumed scale.

## Safe Next Action

Open the script task `ScriptTask_ComputeDiscount` in the BPMN source and audit the `discountRate` calculation expression. Fix the formula so its output is clamped to `[0.0, 1.0]`, or add an upstream guard (e.g., an exclusive gateway) that validates `basePrice` is within the expected range before reaching the script task. After fixing, re-run the debug session to confirm the variable resolves within bounds.

> **No runtime mutation was performed.** This is a read-only diagnosis. Retry or continuation requires explicit user action after the source defect is corrected.
