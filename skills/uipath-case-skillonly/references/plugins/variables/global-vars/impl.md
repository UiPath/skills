# Global Variables — Implementation

Global variables are declared in `root.data.uipath.variables`.

## Declaration

```json
"variables": {
  "inputs": [
    {
      "id": "claimId",
      "name": "claimId",
      "displayName": "Claim ID",
      "type": "string",
      "default": ""
    },
    {
      "id": "claimAmount",
      "name": "claimAmount",
      "displayName": "Claim Amount",
      "type": "number",
      "default": "0"
    }
  ],
  "outputs": [
    {
      "id": "finalDecision",
      "name": "finalDecision",
      "displayName": "Final Decision",
      "type": "string"
    }
  ],
  "inputOutputs": [
    {
      "id": "reviewerComment",
      "name": "reviewerComment",
      "displayName": "Reviewer Comment",
      "type": "string"
    },
    {
      "id": "riskScore",
      "name": "riskScore",
      "displayName": "Risk Score",
      "type": "number"
    }
  ]
}
```

## Referencing in Task Inputs

Pass a global variable as input to a task:

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

## Wiring Task Outputs to Global Variables

Write a task output value into a global variable:

```json
"outputs": [
  {
    "name": "riskScore",
    "displayName": "riskScore",
    "value": "riskScore",
    "type": "number",
    "source": "=riskScore",
    "var": "riskScore",
    "id": "riskScore",
    "target": "=riskScore",
    "elementId": "<stageId>-<taskId>"
  }
]
```

| Output field | Value | Notes |
|---|---|---|
| `name` | Process output name | Matches the output variable name in the process |
| `source` | `"=<outputName>"` | References the process output |
| `var` | Global variable `id` | Which global variable to write to |
| `id` | Same as `var` | Matches the global variable ID |
| `target` | `"=<varId>"` | Expression binding target |
| `value` | Same as `var` | Alias for the variable |

## Expression Syntax

| Expression | Meaning |
|---|---|
| `=vars.claimId` | Read the `claimId` global variable |
| `=vars.reviewerComment` | Read the `reviewerComment` global variable |
| `=js:$vars.claimAmount > 10000` | JavaScript expression using global variable |
| `=js:$vars.region === 'EU'` | Condition using global variable |

> Note the prefix difference: `=vars.` (no `js:`) for direct references; `=js:$vars.` for expressions.

## jsonSchema Type Variable

For complex object outputs:

```json
{
  "id": "caseData",
  "name": "caseData",
  "displayName": "Case Data",
  "type": "jsonSchema",
  "body": {
    "type": "object",
    "properties": {
      "status":  { "type": "string" },
      "message": { "type": "string" }
    }
  },
  "_jsonSchema": {
    "type": "object",
    "properties": {
      "status":  { "type": "string" },
      "message": { "type": "string" }
    }
  }
}
```
