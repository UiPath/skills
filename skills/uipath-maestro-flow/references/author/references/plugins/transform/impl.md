# Transform Node — Implementation

## Node Types and Registry Validation

Supported node types:

- `core.action.transform` — generic; chains operations
- `core.action.transform.filter` — filter only
- `core.action.transform.map` — map only
- `core.action.transform.group-by` — group-by only

Run:

```bash
uip maestro flow registry get core.action.transform --output json
uip maestro flow registry get core.action.transform.filter --output json
uip maestro flow registry get core.action.transform.map --output json
uip maestro flow registry get core.action.transform.group-by --output json
```

Confirm each definition has input port `input`, output ports `output` and `error`, and required inputs `collection` and `operations`. Set each instance's `typeVersion` to the matching response's `version`; do not hardcode it.

For add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the node-specific `inputs` and `model` structures below.

Every transform uses this output schema:

```json
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
}
```

## Collection Input and Output Shape

`inputs.collection` is a transform-specific path containing the array. Use a plain path:

```json
"collection": "$vars.orders.output.items"
```

Never use `=js:` or an inline array literal:

```json
"collection": "=js:$vars.orders.output.items"
```

```json
"collection": "=js:[{\"title\":\"Example\"}]"
```

The runtime resolves the path as a lookup such as `vars.orders.output.items`; `=js:` and inline JSON/JS literals resolve to an empty collection. For static data, put the array in a workflow variable `defaultValue` or emit it from an upstream static-data/script node, then reference that variable or node output.

A transform's `$vars.<transformNode>.output` is a bare array: filter returns surviving elements, map returns mapped elements, and group-by returns group objects (`{<groupByField>, <alias>…}`). Chain transforms from `.output`, never `.output.items`; `.items` becomes `undefined` and silently yields empty input. `.items`/`.body.items` below refer only to HTTP-body or variable shapes.

```json
"collection": "$vars.filterHighViewDays.output"
```

In a Script node, read an element field as `$vars.groupByNode.output[0].totalViews`.

## Generic Transform (`core.action.transform`)

Operations run in order; each feeds the next.

```json
{
  "id": "transformChain",
  "type": "core.action.transform",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "Process Employees" },
  "inputs": {
    "collection": "$vars.fetchData.output.body.employees",
    "operations": [
      {
        "id": "op1", "type": "filter",
        "config": {
          "operation": "and",
          "filters": [
            { "id": "f1", "field": "active", "condition": "equals", "value": true }
          ]
        }
      },
      {
        "id": "op2", "type": "map",
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
    "output": { "type": "object", "description": "The return value of the transform", "source": "=result.response", "var": "output" },
    "error": { "type": "object", "description": "Error information if the transform fails", "source": "=Error", "var": "error" }
  }
}
```

## Filter (`core.action.transform.filter`)

```json
{
  "id": "filterActive",
  "type": "core.action.transform.filter",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "Filter Active Orders" },
  "inputs": {
    "collection": "$vars.orders.output.items",
    "operations": [
      {
        "id": "op1", "type": "filter",
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
    "output": { "type": "object", "description": "The return value of the transform", "source": "=result.response", "var": "output" },
    "error": { "type": "object", "description": "Error information if the transform fails", "source": "=Error", "var": "error" }
  }
}
```

Conditions: `equals`, `not_equals`, `greater_than`, `less_than`, `greater_equal`, `less_equal`, `contains`, `starts_with`, `ends_with`, `is_null`, `is_not_null`.

Operations: `and` (all conditions), `or` (any condition).

`filter.value` is literal-only. It does not evaluate `$vars`, `=js:`, or brace templates; `"$vars.threshold"`, `"=js:$vars.threshold"`, and `"{$vars.threshold}"` are compared as literal strings and silently produce an empty result. Use literal scalars such as `500`, `"active"`, or `true`. For dynamic thresholds, filter in a [Script](../script/impl.md) node or hoist the literal into the flow design. `field` accepts dot-paths such as `order.amount`.

## Map (`core.action.transform.map`)

```json
{
  "id": "mapFields",
  "type": "core.action.transform.map",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "Normalize Names" },
  "inputs": {
    "collection": "$vars.rawData.output.items",
    "operations": [
      {
        "id": "op1", "type": "map",
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
    "output": { "type": "object", "description": "The return value of the transform", "source": "=result.response", "var": "output" },
    "error": { "type": "object", "description": "Error information if the transform fails", "source": "=Error", "var": "error" }
  }
}
```

Transformations: `copy`, `uppercase`, `lowercase`, `trim`.

`keepOriginalFields: false` outputs only mapped fields; `true` passes through unmapped fields. `renameTo` changes the field name; `""` keeps the original name.

## Group By (`core.action.transform.group-by`)

```json
{
  "id": "groupByDept",
  "type": "core.action.transform.group-by",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "Group by Department" },
  "inputs": {
    "collection": "$vars.employees.output.items",
    "operations": [
      {
        "id": "op1", "type": "groupBy",
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
    "output": { "type": "object", "description": "The return value of the transform", "source": "=result.response", "var": "output" },
    "error": { "type": "object", "description": "Error information if the transform fails", "source": "=Error", "var": "error" }
  }
}
```

Aggregation operations:

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

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Filter passes all items through | Wrong condition name, such as `greater` instead of `greater_than` | Use exact names: `equals`, `not_equals`, `greater_than`, `less_than`, `greater_equal`, `less_equal`, `contains`, `starts_with`, `ends_with`, `is_null`, `is_not_null` |
| Filter silently returns empty array | `value` contains an unresolved expression; Transform compares it as a literal string | Use a literal scalar such as `"value": 500`; for dynamic thresholds, use a Script node |
| Collection is null/empty | `collection` uses `=js:` or an inline array literal | Use a plain path such as `"$vars.loadCatalog.output.catalog"` or `"$vars.catalog"`; store static arrays in a variable default or upstream node |
| Map output missing fields | `keepOriginalFields: false` and the field is unmapped | Add the field to mappings or set `keepOriginalFields: true` |
| GroupBy produces empty groups | No items match `groupByField` | Check that `groupByField` matches the actual data fields |
| Chained transform gets empty input although upstream had rows | Used `$vars.<transform>.output.items`; transform output is a bare array | Use `$vars.<transform>.output`; see [Output Shape](#output-shape) |