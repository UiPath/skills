# Diagnosis — debug-fault-777

## Faulting element
`ScriptTask_ComputeDiscount`

## Incident
- Category: `ScriptEvaluation`
- Message: "Script task threw: computed discountRate exceeds the allowed maximum of 1.0."
(source: `uip maestro bpmn debug-instance incidents debug-fault-777 --output json`)

## Offending runtime variable
- `discountRate` = `1.75`
- Related input: `basePrice` = `240`, `orderId` = `ORD-DBG-777`
(source: `uip maestro bpmn debug-instance variables debug-fault-777 --output json` and `variables-all`, scoped to `ScriptTask_ComputeDiscount`)

## Likely root cause
The script logic in `ScriptTask_ComputeDiscount` computed `discountRate` as `1.75`, i.e. a value greater than 1.0 (100%). A discount rate is expected to be a fraction in `[0, 1]`, so this indicates a defect in the script's discount calculation (e.g. a missing division by 100, a wrong tier/multiplier, or an unbounded formula) rather than a transient runtime/infra issue. The runtime's own guard rejected the out-of-range value, raising the incident and faulting the instance.

## Safe next action
Do not retry, cancel, or continue this instance. Route the fix to Author: review and correct the discount-calculation expression/script bound to `ScriptTask_ComputeDiscount` so `discountRate` is clamped/derived to stay within `[0, 1]` for inputs like `basePrice = 240`, then re-run a fresh debug session to confirm the fix before considering any operate action on this faulted instance.
