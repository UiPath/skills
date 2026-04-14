# Transform Node — Implementation

## Node Types

- `core.action.transform` — generic (chains multiple operations)
- `core.action.transform.filter` — filter only
- `core.action.transform.map` — map only
- `core.action.transform.group-by` — group-by only

## Registry Validation

```bash
uip flow registry get core.action.transform --output json
uip flow registry get core.action.transform.filter --output json
uip flow registry get core.action.transform.map --output json
uip flow registry get core.action.transform.group-by --output json
```

Confirm: input port `input`, output ports `output` and `error`, required inputs `collection` and `operations`.

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structures below for the node-specific `inputs` and `model` fields.

---

## Generic Transform (`core.action.transform`)

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
      "source": "=result.Error",
      "var": "error"
    }
  },
  "model": { "type": "bpmn:ScriptTask" }
}
```

---

## Filter (`core.action.transform.filter`)

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
      "source": "=result.Error",
      "var": "error"
    }
  },
  "model": { "type": "bpmn:ScriptTask" }
}
```

**Filter conditions:** `equals`, `not_equals`, `greater`, `greater_equal`, `less`, `less_equal`, `contains`, `not_contains`, `starts_with`, `ends_with`

**Filter operations:** `and` (all conditions must match), `or` (any condition matches)

---

## Map (`core.action.transform.map`)

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
      "source": "=result.Error",
      "var": "error"
    }
  },
  "model": { "type": "bpmn:ScriptTask" }
}
```

**Transformations:** `copy` (no change), `uppercase`, `lowercase`, or a custom expression.

**`keepOriginalFields`:** When `false`, only mapped fields appear in output. When `true`, unmapped fields pass through.

**`renameTo`:** New field name. Empty string (`""`) keeps the original name.

---

## Group By (`core.action.transform.group-by`)

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
      "source": "=result.Error",
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

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Collection is null/empty | `$vars` reference evaluates to null | Check collection expression and upstream output |
| Unknown filter condition | Typo in condition name | Use one of: `equals`, `not_equals`, `greater`, `greater_equal`, `less`, `less_equal`, `contains`, `not_contains`, `starts_with`, `ends_with` |
| Map output missing fields | `keepOriginalFields: false` and field not in mappings | Add the field to mappings or set `keepOriginalFields: true` |
| GroupBy produces empty groups | No items match the group field | Check `groupByField` matches actual field names in the data |
