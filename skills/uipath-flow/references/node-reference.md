# Node Reference

Complete catalog of node types not fully covered in the [architectural planning guide](planning-phase-architectural.md). For OOTB nodes already documented there (Script, HTTP, Decision, Switch, Loop, Merge, End, Terminate, Mock), see the architectural planning guide. For implementation resolution (registry lookups, connection binding, reference field resolution), see the [implementation planning guide](planning-phase-implementation.md).

---

## Data Transform Nodes

Transform nodes operate on arrays — filtering, mapping, grouping, or chaining multiple operations. All share the same port layout (`input` → `output`/`error`) and output their result to `$vars.{nodeId}.output`.

> **Note:** The `collection` input accepts `$vars` references directly (e.g., `$vars.fetchData.output.body.items`). Unlike condition expressions, the `=js:` prefix is optional for `collection` fields — both `$vars.x` and `=js:$vars.x` work.

### Generic Transform (`core.action.transform`)

Chains multiple operations (filter → map → groupBy) in a single node. Operations execute in order; each feeds into the next.

```json
{
  "id": "transformChain",
  "type": "core.action.transform",
  "typeVersion": "1.0.0",
  "display": { "label": "Process Employees" },
  "inputs": {
    "collection": "$vars.fetchData.output.body.employees",
    "operations": [
      {
        "id": "op1",
        "type": "filter",
        "config": {
          "operation": "and",
          "filters": [
            { "id": "f1", "field": "active", "condition": "equals", "value": true }
          ]
        }
      },
      {
        "id": "op2",
        "type": "map",
        "config": {
          "keepOriginalFields": false,
          "mappings": [
            { "id": "m1", "field": "name", "transformation": "uppercase", "renameTo": "fullName" },
            { "id": "m2", "field": "salary", "transformation": "copy", "renameTo": "" }
          ]
        }
      }
    ]
  },
  "model": { "type": "bpmn:ScriptTask" }
}
```

### Filter (`core.action.transform.filter`)

Filters an array based on conditions.

```json
{
  "id": "filterActive",
  "type": "core.action.transform.filter",
  "typeVersion": "1.0.0",
  "display": { "label": "Filter Active Orders" },
  "inputs": {
    "collection": "$vars.orders.output.items",
    "operations": [
      {
        "id": "op1",
        "type": "filter",
        "config": {
          "operation": "and",
          "filters": [
            { "id": "f1", "field": "status", "condition": "equals", "value": "active" },
            { "id": "f2", "field": "amount", "condition": "greater_equal", "value": 100 }
          ]
        }
      }
    ]
  },
  "model": { "type": "bpmn:ScriptTask" }
}
```

**Filter conditions:** `equals`, `not_equals`, `greater`, `greater_equal`, `less`, `less_equal`, `contains`, `not_contains`, `starts_with`, `ends_with`

**Filter operations:** `and` (all conditions must match), `or` (any condition matches)

### Map (`core.action.transform.map`)

Transforms each item in an array by renaming or converting fields.

```json
{
  "id": "mapFields",
  "type": "core.action.transform.map",
  "typeVersion": "1.0.0",
  "display": { "label": "Normalize Names" },
  "inputs": {
    "collection": "$vars.rawData.output.items",
    "operations": [
      {
        "id": "op1",
        "type": "map",
        "config": {
          "keepOriginalFields": false,
          "mappings": [
            { "id": "m1", "field": "firstName", "transformation": "uppercase", "renameTo": "name" },
            { "id": "m2", "field": "email", "transformation": "lowercase", "renameTo": "" },
            { "id": "m3", "field": "dept", "transformation": "copy", "renameTo": "department" }
          ]
        }
      }
    ]
  },
  "model": { "type": "bpmn:ScriptTask" }
}
```

**Transformations:** `copy` (no change), `uppercase`, `lowercase`, or a custom expression.

**`keepOriginalFields`:** When `false`, only mapped fields appear in output. When `true`, unmapped fields pass through.

**`renameTo`:** New field name. Empty string (`""`) keeps the original name.

### Group By (`core.action.transform.group-by`)

Groups array items by a field and applies aggregations.

```json
{
  "id": "groupByDept",
  "type": "core.action.transform.group-by",
  "typeVersion": "1.0.0",
  "display": { "label": "Group by Department" },
  "inputs": {
    "collection": "$vars.employees.output.items",
    "operations": [
      {
        "id": "op1",
        "type": "groupBy",
        "config": {
          "groupByField": "department",
          "aggregations": [
            { "id": "a1", "field": "", "operation": "count", "alias": "headcount" },
            { "id": "a2", "field": "salary", "operation": "sum", "alias": "totalSalary" },
            { "id": "a3", "field": "salary", "operation": "average", "alias": "avgSalary" },
            { "id": "a4", "field": "salary", "operation": "min", "alias": "minSalary" },
            { "id": "a5", "field": "salary", "operation": "max", "alias": "maxSalary" },
            { "id": "a6", "field": "name", "operation": "collect", "alias": "names" },
            { "id": "a7", "field": "name", "operation": "first", "alias": "firstHire" }
          ]
        }
      }
    ]
  },
  "model": { "type": "bpmn:ScriptTask" }
}
```

**Aggregation operations:**

| Operation | Description | `field` required |
|---|---|---|
| `count` | Number of items in group | No |
| `sum` | Sum of numeric field | Yes |
| `average` | Average of numeric field | Yes |
| `min` | Minimum value | Yes |
| `max` | Maximum value | Yes |
| `collect` | Array of all field values | Yes |
| `first` | First item's field value | Yes |
| `last` | Last item's field value | Yes |

---

## Delay Node (`core.logic.delay`)

Pauses execution for a duration or until a specific date. Uses ISO 8601 time formats.

**Ports:** `input` → `output`

### Duration-Based (Preset)

```json
{
  "id": "wait15min",
  "type": "core.logic.delay",
  "typeVersion": "1.0.0",
  "display": { "label": "Wait 15 Minutes" },
  "inputs": {
    "timerType": "timeDuration",
    "timerPreset": "PT15M"
  },
  "model": {
    "type": "bpmn:IntermediateCatchEvent",
    "eventDefinition": "bpmn:TimerEventDefinition"
  }
}
```

### Duration-Based (Custom ISO 8601)

```json
{
  "id": "waitCustom",
  "type": "core.logic.delay",
  "typeVersion": "1.0.0",
  "display": { "label": "Wait 1 Day 5 Hours" },
  "inputs": {
    "timerType": "timeDuration",
    "timerPreset": "custom",
    "timerValue": "P1DT5H30M"
  },
  "model": {
    "type": "bpmn:IntermediateCatchEvent",
    "eventDefinition": "bpmn:TimerEventDefinition"
  }
}
```

### Date-Based (Wait Until)

```json
{
  "id": "waitUntil",
  "type": "core.logic.delay",
  "typeVersion": "1.0.0",
  "display": { "label": "Wait Until April 15" },
  "inputs": {
    "timerType": "timeDate",
    "timerPreset": "custom",
    "timerDate": "=js:$vars.scheduledDate"
  },
  "model": {
    "type": "bpmn:IntermediateCatchEvent",
    "eventDefinition": "bpmn:TimerEventDefinition"
  }
}
```

### Duration Presets

| Preset Value | Duration |
|---|---|
| `PT5M` | 5 minutes |
| `PT15M` | 15 minutes |
| `PT30M` | 30 minutes |
| `PT1H` | 1 hour |
| `PT6H` | 6 hours |
| `PT12H` | 12 hours |
| `P1D` | 1 day |
| `P1W` | 1 week |
| `custom` | Use `timerValue` for custom ISO 8601 duration |

### ISO 8601 Duration Format

`P[n]Y[n]M[n]W[n]DT[n]H[n]M[n]S`

Examples: `PT30S` (30 seconds), `PT2H30M` (2.5 hours), `P3DT12H` (3 days 12 hours)

---

## Subflow Node (`core.subflow`)

Groups nodes into a reusable, drillable container. Subflows have their own variable scope and can be nested up to 3 levels deep.

**Ports:** `input` → `output`, `error`

### Parent Node

```json
{
  "id": "subflow1",
  "type": "core.subflow",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 432, "y": 144 },
    "size": { "width": 96, "height": 96 }
  },
  "display": { "label": "Validate & Transform" },
  "inputs": {
    "inputData": "=js:$vars.fetchData.output.body",
    "threshold": 100
  },
  "model": { "type": "bpmn:SubProcess" }
}
```

### Subflow Definition

Subflow contents are stored in a top-level `subflows` object keyed by the parent node's ID:

```json
{
  "subflows": {
    "subflow1": {
      "nodes": [
        {
          "id": "subflow1Start",
          "type": "core.trigger.manual",
          "typeVersion": "1.0.0",
          "display": { "label": "Start" },
          "inputs": {},
          "model": { "type": "bpmn:StartEvent" }
        },
        {
          "id": "validate",
          "type": "core.action.script",
          "typeVersion": "1.0.0",
          "display": { "label": "Validate" },
          "inputs": {
            "script": "const data = $vars.inputData;\nif (!data || !data.items) throw new Error('Invalid data');\nreturn { valid: true, count: data.items.length };"
          },
          "model": { "type": "bpmn:ScriptTask" }
        },
        {
          "id": "subflow1End",
          "type": "core.control.end",
          "typeVersion": "1.0.0",
          "display": { "label": "End" },
          "inputs": {},
          "outputs": {
            "result": { "source": "=js:$vars.validate.output" }
          },
          "model": { "type": "bpmn:EndEvent" }
        }
      ],
      "edges": [
        {
          "id": "sf-e1",
          "sourceNodeId": "subflow1Start",
          "sourcePort": "output",
          "targetNodeId": "validate",
          "targetPort": "input"
        },
        {
          "id": "sf-e2",
          "sourceNodeId": "validate",
          "sourcePort": "success",
          "targetNodeId": "subflow1End",
          "targetPort": "input"
        }
      ],
      "variables": {
        "globals": [
          {
            "id": "inputData",
            "direction": "in",
            "type": "object"
          },
          {
            "id": "threshold",
            "direction": "in",
            "type": "number",
            "defaultValue": 50
          },
          {
            "id": "result",
            "direction": "out",
            "type": "object"
          }
        ],
        "nodes": []
      }
    }
  }
}
```

### Subflow Rules

- Every subflow **must** have its own Start node (`core.trigger.manual`) and End node (`core.control.end`)
- Subflow `variables.globals` with `direction: "in"` map to the parent node's `inputs`
- Subflow `variables.globals` with `direction: "out"` map to the parent node's outputs, accessible via `$vars.{subflowNodeId}.output`
- Parent-scope `$vars` are **not** visible inside the subflow — pass values explicitly via inputs
- Subflows can be nested (subflow inside subflow), up to 3 levels
- Each subflow has its own `nodes`, `edges`, and `variables` sections

---

## Scheduled Trigger (`core.trigger.scheduled`)

Starts the flow on a recurring schedule using ISO 8601 repeating intervals.

**Ports:** `output` only (it is a start node)

### Preset Frequency

```json
{
  "id": "scheduledStart",
  "type": "core.trigger.scheduled",
  "typeVersion": "1.0.0",
  "display": { "label": "Every Hour" },
  "inputs": {
    "timerType": "timeCycle",
    "timerPreset": "R/PT1H"
  },
  "model": {
    "type": "bpmn:StartEvent",
    "eventDefinition": "bpmn:TimerEventDefinition"
  }
}
```

### Custom Frequency

```json
{
  "id": "scheduledStart",
  "type": "core.trigger.scheduled",
  "typeVersion": "1.0.0",
  "display": { "label": "Every 45 Minutes" },
  "inputs": {
    "timerType": "timeCycle",
    "timerPreset": "custom",
    "timerValue": "R/PT45M"
  },
  "model": {
    "type": "bpmn:StartEvent",
    "eventDefinition": "bpmn:TimerEventDefinition"
  }
}
```

### Frequency Presets

| Preset Value | Frequency |
|---|---|
| `R/PT5M` | Every 5 minutes |
| `R/PT15M` | Every 15 minutes |
| `R/PT30M` | Every 30 minutes |
| `R/PT1H` | Every hour |
| `R/PT6H` | Every 6 hours |
| `R/PT12H` | Every 12 hours |
| `R/P1D` | Daily |
| `R/P1W` | Weekly |
| `custom` | Use `timerValue` for custom ISO 8601 repeating interval |

### ISO 8601 Repeating Interval Format

`R/P[duration]` — `R` means repeat indefinitely, followed by duration.

Examples: `R/PT10M` (every 10 min), `R/P2D` (every 2 days), `R/PT2H30M` (every 2.5 hours)

---

## Queue Nodes

See [orchestration-guide.md — Queue Integration](orchestration-guide.md) for full documentation of `core.action.queue.create` and `core.action.queue.create-and-wait`.

---

## Node Type Quick Reference

| Node Type | Category | Ports (in → out) | Key Inputs |
|---|---|---|---|
| `core.action.transform` | tool | `input` → `output`, `error` | `collection`, `operations[]` |
| `core.action.transform.filter` | tool | `input` → `output`, `error` | `collection`, `operations[{type:"filter"}]` |
| `core.action.transform.map` | tool | `input` → `output`, `error` | `collection`, `operations[{type:"map"}]` |
| `core.action.transform.group-by` | tool | `input` → `output`, `error` | `collection`, `operations[{type:"groupBy"}]` |
| `core.logic.delay` | control-flow | `input` → `output` | `timerType`, `timerPreset`, `timerValue`/`timerDate` |
| `core.subflow` | control-flow | `input` → `output`, `error` | Mapped from subflow `in` variables |
| `core.trigger.scheduled` | trigger | → `output` | `timerType`, `timerPreset`, `timerValue` |
| `core.action.queue.create` | tool | `input` → `output`, `error` | `queue`, `itemData`, `priority` |
| `core.action.queue.create-and-wait` | tool | `input` → `output`, `error` | `queue`, `itemData`, `priority` |
| `uipath.agent.autonomous` | agent | `input` → `output`, `error` | Agent-specific (via registry) |
| `uipath.agent.conversational` | agent | `input` → `output`, `error` | Agent-specific (via registry) |
