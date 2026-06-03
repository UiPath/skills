# Action Task — Planning

Action tasks pause the case and create a human task via a UiPath App (Action Catalog).

## When to Use

| Situation | Use action? |
|---|---|
| Human needs to approve, review, or decide | Yes |
| Human needs to fill in data or validate results | Yes |
| Fully automated processing | No — use a standard-io task |
| Human needs to be notified only (no decision) | No — use SLA escalation notification |

## What You Need Before Building

| Info | Example |
|---|---|
| App name and folder (resourceKey) | `"Shared/Claims.ApprovalApp"` |
| Assignee email, group, or variable | `"reviewer@company.com"` |
| Assignment type | user / group / all |
| Task title shown to human | `"Review Insurance Claim"` |
| Priority | Low / Medium / High / Critical |
| Inputs the human needs to see | e.g., claim details, extracted data |
| Outputs the human will submit | e.g., decision (approved/rejected), comments |

## Binding Resource Value

Action tasks bind to `"resource": "app"` (not `"process"`). Declare both `name` and `folderPath` bindings at root using `"resource": "app"`.

## Recipient Assignment

| `assignmentCriteria` | `recipient` format | Use when |
|---|---|---|
| `"user"` | `{ "Type": 2, "Value": "email@co.com" }` | Assigned to a specific user by email |
| `"user"` | `{ "Type": 0, "Value": "<user-uuid>" }` | Assigned to a specific user by ID |
| `"group"` | `{ "Type": 1, "Value": "<group-uuid>" }` | Assigned to any member of a group |
| `"all"` | `{ "Type": 3, "Value": "=vars.<varId>" }` | Resolved from a variable at runtime |
