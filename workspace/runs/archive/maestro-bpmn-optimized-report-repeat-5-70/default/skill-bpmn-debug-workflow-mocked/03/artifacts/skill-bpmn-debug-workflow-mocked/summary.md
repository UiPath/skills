# OrderApproval Debug Session Summary

## Identifiers

| Field | Value |
|---|---|
| Job Key | `job-debug-042` |
| Instance ID | `debug-run-042` |
| Run ID | `run-042` |
| Solution ID | `sol-042` |
| **Final Status** | **Completed** |

## Runtime Variables

### Process-level (root)

| Variable | Value |
|---|---|
| `orderId` | `"ORD-9001"` |
| `amount` | `1875` |
| `approvalDecision` | `"AutoApproved"` |
| `reviewerTier` | `"Tier2"` |

### Element-scoped — `ScriptTask_Classify`

| Variable | Value |
|---|---|
| `amount` | `1875` |
| `approvalDecision` | `"AutoApproved"` |

## Notes

- The process completed without faults.
- `approvalDecision` was set to `"AutoApproved"` — consistent with an amount of 1875 falling below an auto-approval threshold.
- `reviewerTier` was set to `"Tier2"`, suggesting a secondary reviewer tier was recorded at the process level even though auto-approval was granted.
- All variables were retrieved via `uip maestro bpmn debug-instance variables-all debug-run-042 --output json`.
