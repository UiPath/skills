# OrderApproval Debug Session Summary

## Run identifiers
- Job key: `job-debug-042`
- Instance id: `debug-run-042`
- Run id: `run-042`
- Solution id: `sol-042`

## Inputs
- `orderId`: `ORD-9001`
- `amount`: `1875`

## Final status
**Completed**

## Runtime variables (from `debug-instance variables-all`)

| Variable | Value |
| --- | --- |
| `orderId` | `ORD-9001` |
| `amount` | `1875` |
| `approvalDecision` | `AutoApproved` |
| `reviewerTier` | `Tier2` |

Element-level detail (`ScriptTask_Classify`):
- `amount`: `1875`
- `approvalDecision`: `AutoApproved`

## Notes
Given `orderId = ORD-9001` and `amount = 1875`, the process ran to completion and auto-approved the order (`approvalDecision = AutoApproved`), assigning it to reviewer tier `Tier2`.
