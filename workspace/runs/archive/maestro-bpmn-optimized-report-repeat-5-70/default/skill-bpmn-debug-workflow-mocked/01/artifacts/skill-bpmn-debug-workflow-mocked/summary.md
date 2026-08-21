# OrderApproval Debug Run — Summary

## Run Identifiers

| Field | Value |
|---|---|
| Job Key | `job-debug-042` |
| Instance ID | `debug-run-042` |
| Run ID | `run-042` |
| Solution ID | `sol-042` |
| **Final Status** | **Completed** |

## Runtime Variables

The following variables were observed across the debug session (process scope
and element scope combined via `debug-instance variables-all`):

| Variable | Value | Scope |
|---|---|---|
| `orderId` | `"ORD-9001"` | Process |
| `amount` | `1875` | Process + `ScriptTask_Classify` |
| `approvalDecision` | `"AutoApproved"` | Process + `ScriptTask_Classify` |
| `reviewerTier` | `"Tier2"` | Process |

## Interpretation

The process completed without fault. The `ScriptTask_Classify` element
evaluated the submitted `amount` of **1875** and set `approvalDecision` to
`"AutoApproved"` and `reviewerTier` to `"Tier2"`, indicating the order
fell into the auto-approval tier for that reviewer level.
