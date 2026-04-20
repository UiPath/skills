# Global Variables — Implementation

No CLI command exists for variable declaration. Edit `caseplan.json` directly (read → parse → mutate → write).

## Target Paths

| What | JSON path |
|---|---|
| In argument inputs | `root.data.uipath.variables.inputs[]` |
| Out argument outputs | `root.data.uipath.variables.outputs[]` |
| All internal variables | `root.data.uipath.variables.inputOutputs[]` |
| Trigger output mappings | `nodes[<triggerIndex>].data.uipath.outputs[]` |

Process In arguments first, then Out, then plain variables.

## Uniqueness Rule

Every `var` / `id` must be globally unique across the case. When a name collides, append a counter starting at 2:

```
"decision" exists → "decision2" → "decision3"
"error" + "error2" exist → "error3"
```

The `source` and `name` fields keep the original value — only `var` / `id` / `target` get the suffix.

## Variable Declaration (inputOutputs only)

```json
{ "id": "caseStatus", "name": "caseStatus", "type": "string", "custom": true, "elementId": "root" }
```

| Field | Notes |
|---|---|
| `id` | camelCase, globally unique |
| `type` | `"string"` / `"number"` / `"boolean"` / `"date"` / `"array"` / `"object"` / `"jsonSchema"` |
| `custom` | `true` for user-created variables |
| `elementId` | `"root"` for user-created; `<stageId>-<taskId>` for task outputs |
| `default` | Optional initial value (string-encoded) |
| `body` | `jsonSchema` type only — the schema definition |

## In Argument — 3 entries

1. **Input variable** in `inputs[]` (random 9-char alphanumeric ID)
2. **Companion inputOutput** in `inputOutputs[]` (name-based camelCase ID)
3. **Trigger output mapping** on `triggerNode.data.uipath.outputs[]`

```json
// 1. inputs[]
{ "id": "vkfPdQUYR", "name": "expenseId", "type": "string", "default": "", "elementId": "trigger_aB3cD4" }

// 2. inputOutputs[]
{ "id": "expenseId", "name": "expenseId", "type": "string", "elementId": "trigger_aB3cD4" }

// 3. triggerNode.data.uipath.outputs[]
{ "name": "expenseId", "type": "string", "source": "variables.vkfPdQUYR", "var": "expenseId" }
```

The trigger mapping bridges `inputs[]` to `inputOutputs[]` at runtime. Without it, `=vars.expenseId` would be empty.

## Out Argument — 2 entries

1. **Companion inputOutput** in `inputOutputs[]` (name-based ID, with `default` if specified)
2. **Output variable** in `outputs[]` (random ID, `var` links to companion)

```json
// 1. inputOutputs[]
{ "id": "finalDecision", "name": "finalDecision", "type": "string", "default": "", "elementId": "root" }

// 2. outputs[]
{ "id": "xR7mPqW2k", "name": "finalDecision", "type": "string", "var": "finalDecision" }
```

## InOut Argument

Combines In + Out. Creates input + **one** shared companion IO + trigger mapping + output variable (output omits `var` — the In companion already exists).

## Task Output → inputOutputs Wiring

For every task output written, also append to `root.data.uipath.variables.inputOutputs[]`:

```json
// Task output on the task node
{ "name": "AnomalyCheck", "var": "anomalyCheck", "id": "anomalyCheck",
  "value": "anomalyCheck", "type": "string",
  "source": "=AnomalyCheck", "target": "=anomalyCheck",
  "elementId": "Stage_intake-tAnomalyXX" }

// Corresponding inputOutputs entry on root
{ "id": "anomalyCheck", "name": "AnomalyCheck",
  "type": "string", "elementId": "Stage_intake-tAnomalyXX" }
```

Skip when a `custom: true` output reuses an existing variable from another element.

## Custom Outputs (`custom: true`)

Writes a fixed constant to a global variable when a task completes — not from the task's response.

| Field | Standard Output | Custom Output |
|-------|-----------------|---------------|
| `source` | `"=<fieldName>"` | omitted |
| `value` | variable ID string | `"=<literal>"` or `"=js:<expr>"` |
| `custom` | omitted / `false` | `true` |
| `target` | `"=<varId>"` | omitted |

```json
{ "name": "CustomerStatus", "type": "string",
  "value": "=\"Documents received\"", "custom": true,
  "id": "customerStatus", "var": "customerStatus",
  "elementId": "Stage_pending-tDocAgent" }
```

If the custom output updates an existing variable, skip the `inputOutputs` entry.

## jsonSchema Type

```json
{ "id": "caseData", "name": "caseData", "type": "jsonSchema",
  "body": { "type": "object", "properties": { "status": { "type": "string" } } },
  "_jsonSchema": { "type": "object", "properties": { "status": { "type": "string" } } } }
```

## Expression Syntax

See [bindings-and-expressions.md](../../../bindings-and-expressions.md). Key rule: plain reads use `=vars.x`, comparisons use `=js:vars.x === 'val'`. Never use `$vars.x`.
