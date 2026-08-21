# Diagnosis: debug-fault-777

## Faulting element
`ScriptTask_ComputeDiscount`

## Incident
- Category: `ScriptEvaluation`
- Message: "Script task threw: computed discountRate exceeds the allowed maximum of 1.0."
(`uip maestro bpmn debug-instance incidents debug-fault-777 --output json`)

## Offending runtime variable
`discountRate` = **1.75** (computed from `basePrice` = 240)
(`uip maestro bpmn debug-instance variables debug-fault-777 --output json`)

## Likely root cause
The script task's discount-rate calculation is unconstrained: it produced `discountRate = 1.75`, which is 75% over the allowed maximum of `1.0` (i.e., a >100% discount). The script logic that derives `discountRate` from `basePrice` (and any other inputs) lacks an upper-bound clamp/validation before the value is used, causing the runtime guard in `ScriptTask_ComputeDiscount` to throw.

## Safe next action
No mutation performed. Recommended next step (requires explicit consent before executing): fix the discount-rate calculation in the BPMN source for `ScriptTask_ComputeDiscount` to clamp/validate `discountRate` to the `[0.0, 1.0]` range (or fix the upstream formula/inputs feeding it), then re-run a fresh debug session to confirm the fix — do not retry, cancel, or migrate this faulted debug instance.
