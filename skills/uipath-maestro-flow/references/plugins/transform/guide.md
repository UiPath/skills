# Transform Node — Guide

## Node Types

| Node Type | Description |
| --- | --- |
| `core.action.transform` | Chain multiple operations (filter, map, groupBy) in a single node |
| `core.action.transform.filter` | Filter an array based on conditions |
| `core.action.transform.map` | Transform each item (rename, convert fields) |
| `core.action.transform.group-by` | Group items by a field with aggregations |

## When to Use

Use Transform nodes for declarative map, filter, or group-by on a collection — no custom code needed.

### Selection Heuristics

| Situation | Use Transform? |
| --- | --- |
| Standard filter/map/group-by on an array | Yes |
| Custom logic, string manipulation, computation | No — use [Script](../script/guide.md) |
| Iterate and perform actions per item (API calls, etc.) | No — use [Loop](../loop/guide.md) |

## Ports

All transform variants share the same port layout:

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output`, `error` |

The `error` port is the implicit error port shared with all action nodes — see [Implicit error port on action nodes](../../flow-file-format.md#implicit-error-port-on-action-nodes).

## Output Variables

- `$vars.{nodeId}.output` — the transformed collection

## Key Inputs

| Input | Required | Description |
| --- | --- | --- |
| `collection` | Yes | `$vars` reference to the input array |
| `operations` | Yes | Array of operation objects (filter, map, or groupBy) |

> The `collection` input accepts `$vars` references directly. Unlike condition expressions, the `=js:` prefix is optional — both `$vars.x` and `=js:$vars.x` work.

> **Filter `value` is literal-only.** `core.action.transform.filter`'s per-filter `value` field does NOT resolve `$vars.x`, `=js:`, or brace-template expressions — any such expression ships as a string literal and the filter silently returns an empty array. Only literal scalars work (`500`, `"active"`, `true`). If the threshold must be dynamic, move the filter into a [Script](../script/guide.md) node; keep Transform for static-threshold filters, maps, and group-by.

## Implementation

### Registry Validation

```bash
uip maestro flow registry get core.action.transform --output json
uip maestro flow registry get core.action.transform.filter --output json
uip maestro flow registry get core.action.transform.map --output json
uip maestro flow registry get core.action.transform.group-by --output json
```

Confirm: input port `input`, output ports `output` and `error`, required inputs `collection` and `operations`.

### Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structures below for the node-specific `inputs` and `model` fields.

---

### Generic Transform (`core.action.transform`)

Chains multiple operations (filter -> map -> groupBy) in a single node. Operations execute in order; each feeds into the next.

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
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the transform",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the transform fails",
      "source": "=Error",
      "var": "error"
    }
  },
  "model": { "type": "bpmn:ScriptTask" }
}
```

---

### Filter (`core.action.transform.filter`)

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
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the transform",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the transform fails",
      "source": "=Error",
      "var": "error"
    }
  },
  "model": { "type": "bpmn:ScriptTask" }
}
```

**Filter conditions:** `equals`, `not_equals`, `greater_than`, `less_than`, `greater_equal`, `less_equal`, `contains`, `starts_with`, `ends_with`, `is_null`, `is_not_null`

**Filter operations:** `and` (all conditions must match), `or` (any condition matches)

> **Filter `value` is literal-only — no `$vars`, no `=js:`, no brace-templates.** The Transform runtime reads `value` as-is and does not evaluate expressions. Setting `"value": "$vars.threshold"`, `"value": "=js:$vars.threshold"`, or `"value": "{$vars.threshold}"` silently produces an empty filtered array — the filter is comparing each item's field against the literal string `$vars.threshold` (or `=js:...`), never against the intended number. Only literal scalars work: `"value": 500`, `"value": "active"`, `"value": true`. If you need a dynamic threshold, compute the filter inside a [Script](../script/guide.md) node instead, or hoist the literal into the flow design and keep the Transform filter for demo-time thresholds.

**`field` accepts dot-paths** for nested object fields (e.g., `"field": "order.amount"`). Applies to `collection` elements.

---

### Map (`core.action.transform.map`)

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
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the transform",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the transform fails",
      "source": "=Error",
      "var": "error"
    }
  },
  "model": { "type": "bpmn:ScriptTask" }
}
```

**Transformations:** `copy` (no change), `uppercase`, `lowercase`, `trim` (remove leading/trailing whitespace).

**`keepOriginalFields`:** When `false`, only mapped fields appear in output. When `true`, unmapped fields pass through.

**`renameTo`:** New field name. Empty string (`""`) keeps the original name.

---

### Group By (`core.action.transform.group-by`)

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
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the transform",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the transform fails",
      "source": "=Error",
      "var": "error"
    }
  },
  "model": { "type": "bpmn:ScriptTask" }
}
```

**Aggregation operations:**

| Operation | Description | `field` required |
| --- | --- | --- |
| `count` | Number of items in group | No |
| `sum` | Sum of numeric field | Yes |
| `average` | Average of numeric field | Yes |
| `min` | Minimum value | Yes |
| `max` | Maximum value | Yes |
| `collect` | Array of all field values | Yes |
| `first` | First item's field value | Yes |
| `last` | Last item's field value | Yes |

---

### Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Filter passes all items through | Wrong condition name (e.g. `greater` instead of `greater_than`) | Use exact names: `equals`, `not_equals`, `greater_than`, `less_than`, `greater_equal`, `less_equal`, `contains`, `starts_with`, `ends_with`, `is_null`, `is_not_null` |
| Filter silently returns empty array | Filter `value` holds an unresolved expression (`"$vars.x"`, `"=js:..."`, `"{$vars.x}"`) — Transform compares each item against that string literal | Replace with a literal scalar (`"value": 500`); expressions are not evaluated in filter `value`. If the threshold must be dynamic, do the filter in a Script node |
| Collection is null/empty | `$vars` reference evaluates to null | Check collection expression and upstream output |
| Map output missing fields | `keepOriginalFields: false` and field not in mappings | Add the field to mappings or set `keepOriginalFields: true` |
| GroupBy produces empty groups | No items match the group field | Check `groupByField` matches actual field names in the data |
