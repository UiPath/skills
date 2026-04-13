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

## Recipient Type Reference

| `Type` | `Value` format | Meaning |
|---|---|---|
| `0` | User UUID | Assign by user ID |
| `1` | Group UUID | Assign to any group member |
| `2` | Email string | Assign by email address |
| `3` | `"=vars.<varId>"` | Resolved from variable at runtime |

## Priority Values

`"Low"` `"Medium"` `"High"` `"Critical"`

## assignmentCriteria Values

`"user"` `"group"` `"all"`
