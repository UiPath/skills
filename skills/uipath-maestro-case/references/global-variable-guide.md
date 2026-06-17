# Global Variable Guide

This reference describes how to populate `root.data.uipath.variables.inputOutputs[]` in a case JSON file. The parent skill invokes this procedure after constructing or modifying the case definition.

## Overview

The case JSON tracks all output variables produced by triggers and rule references in `root.data.uipath.variables.inputOutputs[]`. Each entry follows the `UiPathVariable` schema. These represent runtime data slots — each task instance gets its own. This array must be kept in sync with the actual outputs declared across the case — missing entries cause runtime failures.

## UiPathVariable Schema

```typescript
interface UiPathVariable {
  name: string;
  type: string;
  id?: string;
  canonicalId?: string;
  camelizedId?: string;
  displayName?: string;
  subType?: string;
  elementId?: string;
  default?: unknown;
  value?: unknown;
  var?: unknown;
  source?: unknown;
  target?: unknown;
  custom?: boolean;
  internal?: boolean;
  body?: unknown;
  _jsonSchema?: unknown;
}
```

## Variable Collection Sources

### Source 1: Trigger Outputs

Location: `nodes[].data.uipath.outputs[]` where `nodes[].type === "case-management:Trigger"`

Triggers that connect to external services (e.g., `Intsvc.EventTrigger`) produce output variables. Each item in the trigger's `outputs[]` array becomes a variable.

For each trigger node, iterate over `node.data.uipath.outputs[]`. Map each output to a `UiPathVariable`:

| Output field | UiPathVariable field |
|---|---|
| `id` or `var` | `id` |
| `name` | `name` |
| `type` | `type` |
| node `id` | `elementId` |
| `body` | `body` |
| `_jsonSchema` | `_jsonSchema` |

**Example:** A Jira trigger with outputs `response` and `error`:
```json
{
  "id": "response",
  "name": "response",
  "type": "jsonSchema",
  "elementId": "trigger_3WkF0Q",
  "body": { ... }
}
```

### Source 2: Variables Referenced in Rules

Scan entry/exit conditions on stages, tasks, and edges for variable references. Rules that use `rule: "variable-equals"` or similar variable-based conditions reference output variables by ID. If a rule references a variable ID already collected from Source 1, no action is needed. If it references a variable not yet in the collection, add it with the information available from the rule context.

## Variable Collection Procedure

1. Initialize an empty map keyed by variable `id`
2. Iterate over all trigger nodes → collect from `data.uipath.outputs[]`
3. Scan all entry/exit conditions across stages, tasks, and edges for variable references
4. Set `root.data.uipath.variables.inputOutputs` to the collected array

## Orphan Variable Cleanup

After collecting variables, remove orphans — entries that nothing in the case references.

1. Scan the entire case JSON for all variable references by `id` (in rule conditions, task data, etc.)
2. Build a set of referenced variable IDs
3. Remove any entry from `root.data.uipath.variables.inputOutputs[]` whose `id` is not in the referenced set

## Updating the JSON

1. Read the case JSON file
2. Run the variable collection procedure → set `root.data.uipath.variables.inputOutputs`
3. Run orphan variable cleanup
4. Preserve all other fields in the JSON unchanged
5. Write the updated JSON back to the same file path

## Example

**Variables** (from a Jira trigger):
```json
"variables": {
  "inputOutputs": [
    {
      "id": "response",
      "name": "response",
      "type": "jsonSchema",
      "elementId": "trigger_3WkF0Q",
      "body": { "$schema": "http://json-schema.org/draft-07/schema#", "type": "object", "properties": { ... } }
    },
    {
      "id": "error",
      "name": "Error",
      "type": "jsonSchema",
      "elementId": "trigger_3WkF0Q",
      "body": { "type": "object", "properties": { "code": { "type": "string" }, "message": { "type": "string" }, ... } }
    }
  ]
}
```
