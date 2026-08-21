# OrderApproval Debug Session Summary

## Run Identifiers

| Field        | Value           |
|--------------|-----------------|
| Job Key      | `job-debug-042` |
| Instance ID  | `debug-run-042` |
| Run ID       | `run-042`       |
| Solution ID  | `sol-042`       |
| Final Status | **Completed**   |

## Runtime Variables

| Variable           | Value            |
|--------------------|------------------|
| `orderId`          | `ORD-9001`       |
| `amount`           | `1875`           |
| `approvalDecision` | `AutoApproved`   |
| `reviewerTier`     | `Tier2`          |

## Notes

- Inputs supplied: `orderId = "ORD-9001"`, `amount = 1875`.
- The process completed without faults.
- The `ScriptTask_Classify` element produced `approvalDecision = "AutoApproved"` and `reviewerTier = "Tier2"` given the supplied `amount`.
- Variables were read from `debug-instance variables-all` immediately after the session; debug instances are ephemeral.
