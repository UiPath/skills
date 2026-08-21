# OrderApproval Debug Session Summary

## Run Identifiers

- Job key: `job-debug-042`
- Instance ID: `debug-run-042`
- Run ID: `run-042`
- Solution ID: `sol-042`
- **Final status: `Completed`**

## Inputs

- `orderId`: `ORD-9001`
- `amount`: `1875`

## Runtime Variables

From `uip maestro bpmn debug-instance variables-all debug-run-042 --output json`:

| Variable | Value |
| --- | --- |
| `orderId` | `ORD-9001` |
| `amount` | `1875` |
| `approvalDecision` | `AutoApproved` |
| `reviewerTier` | `Tier2` |

### Per-element variables (`ScriptTask_Classify`)

| Variable | Value |
| --- | --- |
| `amount` | `1875` |
| `approvalDecision` | `AutoApproved` |

## Interpretation

The debug run completed successfully end-to-end. Based on the order amount (1875), the process classified the order as `AutoApproved` and assigned it to `Tier2` for review.
