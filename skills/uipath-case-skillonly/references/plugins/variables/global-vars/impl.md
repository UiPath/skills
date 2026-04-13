# Global Variables — Implementation

Global variables are declared in `root.data.uipath.variables`.

## Variable Names Must Be Unique Across the Case

Every variable name (the `var` / `id` / `name` field on a task output, and every entry in `root.data.uipath.variables.*`) must be **globally unique within the case**. This applies regardless of which task produces the variable — two different tasks cannot both declare `var: "decision"`.

### Uniqueness rule (matches the FE designer)

The FE source (`NameUtil.ts:58-70` `toUniqueCamelCase`) generates unique names by appending a counter starting at **2** when the desired name already exists:

```
desired: "decision"
existing: ["claimId", "decision"]
result:   "decision2"

desired: "error"
existing: ["claimId", "error", "error2"]
result:   "error3"
```

### Build procedure

When writing each task output:

1. Maintain a running set of all `var` / `id` / `name` values used so far in the case (across all tasks and all `inputOutputs` entries).
2. CamelCase the desired name from the task spec (e.g., `Reviewer Comment` → `reviewerComment`).
3. If the name is already in the set, append a counter starting at 2 (`reviewerComment` → `reviewerComment2` → `reviewerComment3` → …).
4. Use the resulting unique name as `var`, `id`, and `name` on the output declaration. Use `=<originalSourceField>` for `source` (the source field on the task itself never changes — only the global var name is suffixed).
5. Add the unique name to the set.

> **Standard `Error` output exception**: every standard-IO task gets an Error output. Apply the same uniqueness rule: first task gets `var: "error"`, second `error2`, third `error3`, etc. The `source: "=Error"` and `name: "Error"` fields on the output entry stay literal — only the `var` / `id` / `target` fields get the counter suffix.

### Wrong (will cause variable collision in the runtime)

```json
// Task A
{ "name": "decision", "var": "decision", "id": "decision", "source": "=Decision", ... }
// Task B
{ "name": "decision", "var": "decision", "id": "decision", "source": "=Decision", ... }  // ❌ same var name
```

### Right

```json
// Task A — first to declare 'decision'
{ "name": "decision", "var": "decision", "id": "decision", "source": "=Decision", ... }
// Task B — name collides, append counter
{ "name": "decision", "var": "decision2", "id": "decision2", "source": "=Decision", ... }
```

The display `name` may be the same; only the global `var` / `id` need to differ. Downstream consumers reference the unique var: `=vars.decision2`.

## When to Populate `inputOutputs`

The FE designer populates `root.data.uipath.variables.inputOutputs` automatically every time a task's outputs change (`mutateRootVariables` in `VariableMutationUtils.ts`). To produce caseplan.json files that match what the FE emits, **the skill MUST populate `inputOutputs` for every task output it writes** — one entry per unique global variable.

| Source of the variable | Action |
|---|---|
| Output of a task (`task.data.outputs[]` with `var`/`source`/`target` set) | **Add an `inputOutputs` entry** mirroring that output (see shape below). One entry per unique `var`/`id`. |
| Output marked `custom: true` whose `var` points to an existing `inputOutputs` entry from a different element (or a system variable on the same element) | **Skip** — this is an "update existing" output that reuses an existing variable. Adding a duplicate would break the reference. |
| Case input from caller (parent case or external trigger) | Add to `inputs` |
| Case output back to caller (returned to invoking process) | Add to `outputs` |
| Manually introduced (no producing task — set by external API or default) | Add to whichever bucket fits its lifecycle (`inputs` / `outputs` / `inputOutputs`) |

> Older caseplan.json files may have an empty `inputOutputs: []` despite containing tasks with outputs. The runtime tolerates this for backward compatibility, but new files written by the skill should populate it to match current FE behavior — the variable picker in the designer relies on these entries to surface `vars.*` to downstream tasks.

### `inputOutputs` Entry Shape

Each entry mirrors a task output but with a global-scope perspective. Source: `VariableMutationUtils.ts:134-147`.

```json
{
  "id": "<unique varId>",        // matches the task output's `var` field; obeys uniqueness rule above
  "name": "<originalName>",      // matches the task output's `name` field (NOT camelCased / NOT counter-suffixed)
  "type": "string",              // primitive type, "jsonSchema", "file", "json", etc.
  "elementId": "<stageId>-<taskId>",  // back-reference to the producing task
  "body": { ... }                // present only for jsonSchema/file types — the schema body
}
```

Optional fields the FE may emit when applicable: `subType`, `custom`, `internal`. Omit when not relevant.

### Build Procedure

When writing each task output, also push a corresponding `inputOutputs` entry:

1. Determine the unique `var` name (apply the [uniqueness rule](#variable-names-must-be-unique-across-the-case) above).
2. Write the task output entry with that `var` / `id`.
3. Append an `inputOutputs` entry to `root.data.uipath.variables.inputOutputs`:
   - `id` = the unique `var` from step 1
   - `name` = the original (non-suffixed) task output `name`
   - `type` = the task output's `type`
   - `elementId` = `<stageId>-<taskId>` of the producing task
   - `body` = task output's `_jsonSchema` (for `type: "jsonSchema"`) or the file-schema body
4. Skip step 3 if the output is "update existing" (`custom: true` AND `var` references a pre-existing `inputOutputs` entry from another element).

### Worked Example

Task output:
```json
{ "name": "AnomalyCheck", "var": "anomalyCheck", "id": "anomalyCheck",
  "value": "anomalyCheck", "type": "string",
  "source": "=AnomalyCheck", "target": "=anomalyCheck",
  "elementId": "Stage_intake-tAnomalyXX" }
```

Corresponding `inputOutputs` entry on root:
```json
{ "id": "anomalyCheck", "name": "AnomalyCheck",
  "type": "string", "elementId": "Stage_intake-tAnomalyXX" }
```

For an Error output (jsonSchema):
```json
// Task output
{ "name": "Error", "var": "error3", "id": "error3", "value": "error",
  "type": "jsonSchema", "source": "=Error", "target": "=error",
  "elementId": "Stage_intake-tIncidentYY",
  "body": { ... } }

// Root inputOutputs entry
{ "id": "error3", "name": "Error",
  "type": "jsonSchema", "elementId": "Stage_intake-tIncidentYY",
  "body": { ... } }
```

Notice: `id` carries the unique counter suffix (`error3`); `name` keeps the original (`Error`).

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

| Expression | Use in | Notes |
|---|---|---|
| `=vars.claimId` | Task `input.value`, plain variable reads | Legacy/short form — direct read of a variable |
| `=js:vars.claimAmount > 10000` | `conditionExpression` on rules; SLA `expression` | Canonical JavaScript form — required for any computation or comparison |
| `=js:vars.region === 'EU'` | `conditionExpression` | Comparison expression — must use `=js:` |
| `=string.Format("Claim {0}", vars.id)` | `taskTitle`, `caseAppConfig.caseSummary` | C#-style string template (NOT JavaScript) |

> **Variable accessor is `vars.x`** (no `$`). The `$vars.x` syntax does not exist in the runtime.
>
> **Prefix selection rule** (matches FE `addJavascriptPrefix` in `EditorUtil.ts`):
> - Plain variable read in a task input → `=vars.x` is fine
> - Any expression / comparison / function call → must be `=js:...`
> - String template → `=string.Format(...)`
>
> The runtime accepts both `=vars.x ...` and `=js:vars.x ...` for `conditionExpression` (legacy compat), but new code emitted by the FE always uses `=js:`. Match that for forward compatibility.

## Custom Output Values (`custom: true`)

A "custom" output is a user-defined constant value that is written to a global variable when the task completes — it does NOT come from the task's actual response. This is used when you need to set a variable to a fixed value based on which task completed, rather than extracting data from the task output.

### When to Use

- Setting a status flag when a task completes (e.g., `="Customer submitted required documents"`)
- Writing a constant value that downstream conditions can check
- Marking which path the case took through a branching flow

### Custom Output Shape

```json
{
  "name": "Pendingwithcustomeroutput",
  "displayName": "Pendingwithcustomeroutput",
  "type": "string",
  "value": "=\"Customer submitted required documents\"",
  "custom": true,
  "id": "pendingwithcustomeroutput",
  "var": "pendingwithcustomeroutput",
  "elementId": "Stage_BYTjxD-p3kZn9OyG"
}
```

Key differences from standard outputs:

| Field | Standard Output | Custom Output |
|-------|-----------------|---------------|
| `source` | `"=<fieldName>"` (reads from task response) | omitted |
| `value` | variable ID string | `"=<literal>"` or `"=js:<expression>"` |
| `custom` | omitted or `false` | `true` |
| `target` | `"=<varId>"` | omitted (value IS the target) |

### inputOutputs Entry for Custom Outputs

Custom outputs that create a NEW variable still need an `inputOutputs` entry:

```json
{
  "id": "pendingwithcustomeroutput",
  "name": "Pendingwithcustomeroutput",
  "type": "string",
  "elementId": "Stage_BYTjxD-p3kZn9OyG",
  "custom": true
}
```

If the custom output **updates an existing variable** (one already declared by another task), skip the `inputOutputs` entry — the variable already exists.

### Example: Marking Stage Completion Path

Task in "Pending with customer" ExceptionStage writes a constant when it completes:

```json
// Task output
{
  "name": "CustomerStatus",
  "displayName": "CustomerStatus",
  "type": "string",
  "value": "=\"Documents received\"",
  "custom": true,
  "id": "customerStatus",
  "var": "customerStatus",
  "elementId": "Stage_pending-tDocAgent"
}
```

Downstream condition checks this value:

```json
{
  "rule": "selected-stage-exited",
  "selectedStageId": "Stage_pending",
  "conditionExpression": "=js:vars.customerStatus === 'Documents received'"
}
```

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
