# OrderApproval Debug Session Summary

## Session Identifiers

| Field       | Value          |
|-------------|----------------|
| Job Key     | `job-debug-042` |
| Instance ID | `debug-run-042` |
| Run ID      | `run-042`       |
| Solution ID | `sol-042`       |

## Final Status

**Completed**

## Runtime Variables

| Variable           | Value           |
|--------------------|-----------------|
| `orderId`          | `ORD-9001`      |
| `amount`           | `1875`          |
| `approvalDecision` | `AutoApproved`  |
| `reviewerTier`     | `Tier2`         |

## Notes

- The debug session ran to completion with no incidents.
- Input variables (`orderId`, `amount`) are present at runtime with their supplied values.
- The process produced two output variables: `approvalDecision` was set to `AutoApproved` and `reviewerTier` was set to `Tier2`, indicating the order was automatically approved and assigned to a Tier 2 reviewer.
