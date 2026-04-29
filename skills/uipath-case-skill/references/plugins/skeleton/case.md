# Case Skeleton — Implementation

## Write caseplan.json Directly

**Never** run `uip case cases add`, instead, directly write to <directory>/<solutionName>/<projectName>/caseplan.json:

```json
{
  "root": {
    "id": "root",
    "name": "<Case Name>",
    "type": "case-management:root",
    "caseIdentifier": "<identifier>",
    "caseIdentifierType": "constant",
    "caseAppEnabled": true,
    "version": "v16",
    "publishVersion": 2,
    "description": "<case description>",
    "data": {
      "uipath": {
        "bindings": [],
        "variables": {
          "inputs": [],
          "outputs": [],
          "inputOutputs": []
        }
      },
      "slaRules": [],
      "intsvcActivityConfig": "v2"
    },
    "caseAppConfig": {
      "caseSummary": "",
      "sections": []
    },
    "caseExitConditions": []
  },
  "nodes": [],
  "edges": []
}
```

### Root field reference

| Field | Required | Notes |
|---|---|---|
| `version` | yes | Always `"v16"` |
| `publishVersion` | yes | Currently `2` |
| `caseAppEnabled` | yes | Default `true`. Set `false` only if user explicitly opts out |
| `caseAppConfig` | when `caseAppEnabled=true` | See below. Empty defaults are valid |
| `data.intsvcActivityConfig` | yes | Currently `"v2"` |
| `data.slaRules` | no | Case-level SLA + escalation, see `plugins/sla` |
| `caseExitConditions` | yes | At least one — see `plugins/conditions/case-exit` |

### Case App Config

`caseAppConfig` populates the auto-generated Case App UI shown to case workers:

```json
"caseAppConfig": {
  "caseSummary": "=string.Format(\"{0} - {1}\", vars.response.customerName, vars.response.policyId)",
  "sections": [
    {
      "id": "section-<uuid>",
      "title": "Applicant",
      "details": "{\"Name\":\"=vars.response.customerName\",\"Email\":\"=vars.response.customerEmail\"}"
    }
  ]
}
```

| Field | Notes |
|---|---|
| `caseSummary` | Expression rendered as case header. Use `=string.Format(...)` or `=vars.x` |
| `sections[].id` | `section-<uuid>` (any unique string) |
| `sections[].title` | Card heading shown to case worker |
| `sections[].details` | **JSON-encoded string** — keys are field labels, values are expressions. Parsed at render time |

If the user does not specify case app fields, write empty defaults (`caseSummary: ""`, `sections: []`) — leaving `caseAppConfig` absent breaks the UI when `caseAppEnabled: true`.
