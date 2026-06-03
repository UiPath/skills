# Hook Input Guide

This reference describes how to populate input values for all task types in a case management JSON file. The parent skill invokes this procedure after building the task JSON structure (see `task-json-builder-guide.md`).

## Non-Connector Tasks (process, action, agent, api-workflow, case-management)

Each input has a `value` field. Set it to the desired string value. Leave as `""` if no value is needed.

```json
{
  "name": "Content",
  "displayName": "Content",
  "value": "Hello world",
  "type": "string",
  "id": "v3YSGGSc9",
  "var": "v3YSGGSc9",
  "elementId": "stage_1-tNEHpGDYd"
}
```

Use `uip case tasks describe` to discover available inputs:

```bash
uip case tasks describe --type <TASK_TYPE> --id <ENTITY_KEY> --output json
```

---

## Connector Activity Inputs (execute-connector-activity)

Use `uip case tasks describe` to discover available inputs:

```bash
uip case tasks describe --type connector-activity --id <ACTIVITY_TYPE_ID> --connection-id <CONNECTION_UUID> --output json
```

Activity inputs are structured as JSON objects. Values are set inside `input.body` (not `input.value`). There are up to three input types:

### `body` — Request body fields

Contains the main request fields. Each key in `body` is a field name with an empty string as default.

```json
{
  "name": "body",
  "type": "json",
  "target": "body",
  "body": { "comment": "", "summary": "", "description": "" },
  "var": "vRaNdOmId",
  "id": "vRaNdOmId",
  "elementId": "stage_1-tABCDEFGH"
}
```

To set values, populate the fields in `body`:

```json
{
  "name": "body",
  "type": "json",
  "target": "body",
  "body": { "comment": "Hello world", "summary": "Bug report", "description": "Steps to reproduce..." },
  "var": "vRaNdOmId",
  "id": "vRaNdOmId",
  "elementId": "stage_1-tABCDEFGH"
}
```

### `pathParameters` — URL path parameters

Contains parameters embedded in the API path (e.g., issue ID).

```json
{
  "name": "pathParameters",
  "type": "json",
  "target": "pathParameters",
  "body": { "issueIdOrKey": "" },
  "var": "vRaNdOm02",
  "id": "vRaNdOm02",
  "elementId": "stage_1-tABCDEFGH"
}
```

To set values:

```json
{
  "name": "pathParameters",
  "type": "json",
  "target": "pathParameters",
  "body": { "issueIdOrKey": "PROJ-123" },
  "var": "vRaNdOm02",
  "id": "vRaNdOm02",
  "elementId": "stage_1-tABCDEFGH"
}
```

### `queryParameters` — URL query parameters

Contains query string parameters.

```json
{
  "name": "queryParameters",
  "type": "json",
  "target": "queryParameters",
  "body": { "expand": "" },
  "var": "vRaNdOm03",
  "id": "vRaNdOm03",
  "elementId": "stage_1-tABCDEFGH"
}
```

### How values are merged

Values are keyed by input name and shallow-merged into the corresponding `input.body`. Existing fields from enrichment are preserved; provided values overwrite matching keys.

```
Given input values: {"body": {"comment": "Hello"}, "queryParameters": {"issueIdOrKey": "PROJ-123"}}

inputs[name="body"].body           = { ...existingFields, "comment": "Hello" }
inputs[name="queryParameters"].body = { ...existingFields, "issueIdOrKey": "PROJ-123" }
```

**Full example:**

```
enrichment skeleton:
  inputs[name="body"].body = { "comment": "", "summary": "" }

provided values:
  { "body": { "comment": "Hello" } }

result:
  inputs[name="body"].body = { "comment": "Hello", "summary": "" }
```

Not all inputs are present for every activity. The `describe` response shows which inputs exist. Only `body` is always present if the activity has request fields.

---

## Connector Trigger Inputs (wait-for-connector)

Use `uip case tasks describe` to discover available parameters:

```bash
uip case tasks describe --type connector-trigger --id <TRIGGER_TYPE_ID> --connection-id <CONNECTION_UUID> --output json
```

Trigger inputs have a single `body` input with a different structure from activity inputs.

### Structure

```json
{
  "name": "body",
  "type": "json",
  "target": "body",
  "body": {
    "filters": { "expression": "" },
    "parameters": { "project": "", "issuetype": "" }
  },
  "var": "vRaNdOmId",
  "id": "vRaNdOmId"
}
```

### `parameters` — Event parameters

Key/value pairs that filter which events trigger the case. The available parameter names come from the `describe` response.

To set values, populate the parameter fields:

```json
"parameters": { "project": "ACEDU", "issuetype": "19238" }
```

### `filters.expression` — Event filter expression

An optional filter expression that further constrains which events trigger the case. Uses a bracket-based expression syntax.

```json
"filters": { "expression": "((fields.progress<`222`))" }
```

Leave as `""` if no filter is needed.

### How values are populated

Event parameters are passed as flat key/value pairs — all values are strings. They populate `body.parameters` directly. The filter expression is a separate field in `body.filters.expression`.

**Example — Jira trigger filtering by project and issue type:**

```json
{
  "name": "body",
  "type": "json",
  "target": "body",
  "body": {
    "filters": { "expression": "" },
    "parameters": { "project": "ACEDU", "issuetype": "19238" }
  }
}
```

---

## Event Trigger Inputs (trigger node)

Event triggers on the trigger node (not in a stage) use the same input structure as wait-for-connector tasks above, except:

- No `elementId` on the input (trigger inputs don't carry elementId)
- Same `body.parameters` and `body.filters.expression` structure

See `trigger-json-builder-guide.md` for the full trigger node JSON.

---

## Required Fields

The `describe` response may include `requiredFields` on inputs, listing which sub-fields must be populated:

```json
{
  "name": "body",
  "type": "json",
  "body": { "comment": "", "summary": "" },
  "requiredFields": ["summary"]
}
```

This means `summary` must have a non-empty value. `requiredFields` is informational — strip it from the task JSON (it is not part of the task data structure), but use it to ensure required values are provided.

---

## Input Value Formats

Input values are not limited to plain strings. The case management runtime supports several expression formats, detected by prefix. This applies to both `input.value` (non-connector tasks) and values inside `input.body` fields (connector tasks).

### String Literal (no prefix)

Plain text with no `=` prefix. Used for hardcoded constant values.

```
"value": "Hello world"
"value": "123"
"value": "true"
```

### Global Variable Reference (`=vars.`)

Reference a process-level variable or a task output that has been hoisted to root `inputOutputs`. This is the primary way to pass data between tasks.

```
"value": "=vars.userId"
"value": "=vars.response.fields.summary"
"value": "=vars.error.message"
```

Supports nested property access via dot notation and bracket notation for special characters:

```
"value": "=vars.response.data.customer[\"account-id\"]"
"value": "=vars.items[0].name"
```

### Case Metadata Reference (`=metadata.`)

Reference case-level metadata fields.

```
"value": "=metadata.caseId"
"value": "=metadata.caseOwner"
```

### JavaScript Expression (`=js:`)

Full JavaScript expression for complex calculations. Has access to `vars.*` for variable references.

```
"value": "=js:vars.quantity * vars.price"
"value": "=js:vars.items.filter(x => x.status === 'active').length"
"value": "=js:vars.amount > 1000 ? 'VIP' : 'Standard'"
```

### Binding Reference (`=bindings.`)

Reference a binding value. Typically used in `data.name`, `data.folderPath`, and connector context — not in task inputs directly.

```
"value": "=bindings.bXYZ1234"
```

### Data Fabric Reference (`=datafabric.`)

Reference Data Fabric entity fields. Available when Data Fabric is enabled for the case.

```
"value": "=datafabric.Customer.Name"
"value": "=datafabric.Customer.Email"
```

### Job Attachment Reference (`=orchestrator.JobAttachments`)

Reference file attachments from Orchestrator. Used for file-type inputs.

```
"value": "=orchestrator.JobAttachments"
```

### Summary

| Format | Prefix | Example | Use case |
|---|---|---|---|
| String literal | none | `Hello world` | Hardcoded constants |
| Global variable | `=vars.` | `=vars.userId` | Task outputs, process variables |
| Metadata | `=metadata.` | `=metadata.caseId` | Case-level data |
| JavaScript | `=js:` | `=js:vars.a + vars.b` | Complex calculations |
| Binding | `=bindings.` | `=bindings.bXYZ` | Resource references |
| Data Fabric | `=datafabric.` | `=datafabric.Customer.Name` | Entity data |
| Job attachment | `=orchestrator.` | `=orchestrator.JobAttachments` | File references |

The `=` prefix signals an expression. Values without `=` are treated as string literals.
