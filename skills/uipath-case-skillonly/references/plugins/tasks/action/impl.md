# Action Task — Implementation

## Step 1 — Declare Bindings at Root Level

Action tasks use `"resource": "app"` (not `"process"`):

```json
{
  "id": "b<8chars>",
  "name": "name",
  "type": "string",
  "resource": "app",
  "propertyAttribute": "name",
  "resourceKey": "Shared/Claims.ApprovalApp",
  "default": "ApprovalApp"
},
{
  "id": "b<8chars>",
  "name": "folderPath",
  "type": "string",
  "resource": "app",
  "propertyAttribute": "folderPath",
  "resourceKey": "Shared/Claims.ApprovalApp",
  "default": "Shared/Claims"
}
```

## Step 2 — Write the Task

```json
{
  "id": "t<8chars>",
  "elementId": "<stageId>-t<8chars>",
  "displayName": "Approve Claim",
  "description": "Human reviewer approves or rejects the claim.",
  "type": "action",
  "isRequired": true,
  "shouldRunOnlyOnce": true,
  "data": {
    "name": "=bindings.<nameBindingId>",
    "folderPath": "=bindings.<folderBindingId>",
    "taskTitle": "Review Insurance Claim",
    "priority": "Medium",
    "assignmentCriteria": "user",
    "recipient": {
      "Type": 2,
      "Value": "reviewer@company.com"
    },
    "inputs": [
      {
        "name": "claim_details",
        "displayName": "claim_details",
        "value": "=vars.claimId",
        "type": "string",
        "id": "claim_details",
        "elementId": "<stageId>-<taskId>"
      }
    ],
    "outputs": [
      {
        "name": "Action",
        "displayName": "Action",
        "value": "action",
        "type": "string",
        "source": "=Action",
        "var": "action",
        "id": "action",
        "target": "=action",
        "elementId": "<stageId>-<taskId>"
      },
      {
        "name": "reviewer_comment",
        "displayName": "reviewer_comment",
        "value": "reviewerComment",
        "type": "string",
        "source": "=reviewer_comment",
        "var": "reviewerComment",
        "id": "reviewerComment",
        "target": "=reviewerComment",
        "elementId": "<stageId>-<taskId>"
      }
    ]
  },
  "entryConditions": [
    {
      "id": "Condition_<6chars>",
      "displayName": "Stage entered",
      "rules": [[{ "rule": "current-stage-entered", "id": "Rule_<6chars>" }]]
    }
  ]
}
```

## Action Task `data` Fields

| Field | Required | Notes |
|---|---|---|
| `name` / `folderPath` | ✓ | App bindings (`resource: "app"`) — Step 1 above |
| `taskTitle` | ✓ | Display title shown in Action Center; can be a JS expression like `=string.Format("{0}", vars.x)` |
| `priority` | optional | One of `"Low"` `"Medium"` `"High"` `"Critical"` (default `"Medium"`) |
| `recipient` | optional | If absent, the task can be claimed by any user in the assigned scope. See Recipient Type Reference below. |
| `assignmentCriteria` | optional | One of `"user"` `"group"` `"all"`. **Auto-computed from `recipient.Type` if omitted** (Type 0 → `user`, Type 1 → `group`). Leave it out if you let the runtime decide. |
| `enableActionableNotifications` | optional | Boolean. When `true`, notifications sent for this task (Slack, Teams, Outlook) include inline action buttons (Approve/Reject) so the recipient can act without opening the Action Center. Defaults to `false`/absent. |
| `inputs` | optional | Bound inputs to the SimpleApproval (or custom) app form |
| `outputs` | ✓ | At minimum, capture the user's decision (`Action`) |

### Recipient Type Reference

| `Type` | `Value` format | Meaning |
|---|---|---|
| `0` | User UUID | Assign by user ID |
| `1` | Group UUID | Assign to any group member |
| `2` | Email string | Assign by email address |
| `3` | `"=vars.<varId>"` | Resolved from variable at runtime |

### Optional-Field Examples

```json
// Minimal: title + priority, anyone in tenant can claim
"data": {
  "name": "=bindings.<n>", "folderPath": "=bindings.<f>",
  "taskTitle": "Review claim",
  "priority": "Medium",
  "inputs": [], "outputs": [...]
}

// With actionable notifications + dynamic title from prior task output
"data": {
  "name": "=bindings.<n>", "folderPath": "=bindings.<f>",
  "taskTitle": "=string.Format(\"Review {0}\", vars.response.policyId)",
  "priority": "High",
  "enableActionableNotifications": true,
  "inputs": [...], "outputs": [...]
}
```
