# Transform Node — Planning

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
| Custom logic, string manipulation, computation | No — use [Script](../script/planning.md) |
| Iterate and perform actions per item (API calls, etc.) | No — use [Loop](../loop/planning.md) |

## Ports

All transform variants share the same port layout:

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output`, `error` |

## Output Variables

- `$vars.{nodeId}.output` — the transformed collection

## Key Inputs

| Input | Required | Description |
| --- | --- | --- |
| `collection` | Yes | `$vars` reference to the input array |
| `operations` | Yes | Array of operation objects (filter, map, or groupBy) |

> The `collection` input accepts `$vars` references directly. Unlike condition expressions, the `=js:` prefix is optional — both `$vars.x` and `=js:$vars.x` work.
