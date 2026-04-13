# Standard IO Tasks — Implementation

Covers `process`, `agent`, `rpa`, `api-workflow`, `case-management`. All five use the same JSON structure — only the `type` field differs.

## Step 1 — Declare Bindings at Root Level

Add two binding entries to `root.data.uipath.bindings` for every standard-IO task:

```json
{
  "id": "b<8chars>",
  "name": "name",
  "type": "string",
  "resource": "process",
  "propertyAttribute": "name",
  "resourceKey": "Shared/[CM] Insurance.BookAppraisal",
  "default": "BookAppraisal"
},
{
  "id": "b<8chars>",
  "name": "folderPath",
  "type": "string",
  "resource": "process",
  "propertyAttribute": "folderPath",
  "resourceKey": "Shared/[CM] Insurance.BookAppraisal",
  "default": "Shared/[CM] Insurance"
}
```

Generate a fresh `b<8chars>` ID for each binding entry.

## Step 2 — Write the Task in the Stage

```json
{
  "id": "t<8chars>",
  "elementId": "<stageId>-t<8chars>",
  "displayName": "Book Appraisal",
  "description": "Runs the RPA appraisal process.",
  "type": "rpa",
  "isRequired": true,
  "shouldRunOnlyOnce": true,
  "data": {
    "name": "=bindings.<nameBindingId>",
    "folderPath": "=bindings.<folderBindingId>",
    "inputs": [],
    "outputs": [
      {
        "name": "Error",
        "displayName": "Error",
        "value": "error",
        "type": "jsonSchema",
        "source": "=Error",
        "var": "error",
        "id": "error",
        "target": "=error",
        "elementId": "<stageId>-<taskId>",
        "body": {
          "type": "object",
          "properties": {
            "code":     { "type": "string" },
            "message":  { "type": "string" },
            "detail":   { "type": "string" },
            "category": { "type": "string" },
            "status":   { "type": "number" },
            "element":  { "type": "string" }
          }
        },
        "_jsonSchema": {
          "type": "object",
          "properties": {
            "code":     { "type": "string" },
            "message":  { "type": "string" },
            "detail":   { "type": "string" },
            "category": { "type": "string" },
            "status":   { "type": "number" },
            "element":  { "type": "string" }
          }
        }
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

> Always include the `Error` output. Omit the `inputs` array entries if no inputs are needed (keep `"inputs": []`).

## Adding Task Inputs (Wiring from Global Variables)

```json
"inputs": [
  {
    "name": "claimId",
    "displayName": "claimId",
    "value": "=vars.claimId",
    "type": "string",
    "id": "claimId",
    "elementId": "<stageId>-<taskId>"
  }
]
```

## Adding Task Outputs (Wiring to Global Variables)

```json
"outputs": [
  {
    "name": "approvalResult",
    "displayName": "approvalResult",
    "value": "approvalStatus",
    "type": "string",
    "source": "=approvalResult",
    "var": "approvalStatus",
    "id": "approvalStatus",
    "target": "=approvalStatus",
    "elementId": "<stageId>-<taskId>"
  },
  { ... Error output ... }
]
```

> `source` is the output variable name from the process (prefixed with `=`). `var` and `id` are the global variable IDs to write into.

## Type Reference

| `type` value | Use for |
|---|---|
| `"process"` | Agentic / orchestration process |
| `"agent"` | AI agent |
| `"rpa"` | RPA desktop/browser automation |
| `"api-workflow"` | Published API workflow |
| `"case-management"` | Nested case management process |
