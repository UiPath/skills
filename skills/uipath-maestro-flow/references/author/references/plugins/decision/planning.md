# Decision Node — Planning

## Node Type

`core.logic.decision`

## When to Use

Use a Decision node for binary branching (if/else) based on a boolean condition.

### Selection Heuristics

| Situation | Use Decision? |
| --- | --- |
| Two-path branch based on a boolean condition | Yes |
| Three or more paths | No — use [Switch](../switch/planning.md) |
| Branch on HTTP response status codes | No — use [HTTP](../http/planning.md) built-in branches |
| Branch requires reasoning on ambiguous input | No — use [Agent](../agent/planning.md) |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `true`, `false` |

## Key Inputs

| Input | Required | Description |
| --- | --- | --- |
| `expression` | Yes | Boolean JavaScript expression (e.g., `$vars.fetchData.output.statusCode === 200`) |
| `trueLabel` | No | Custom label for the true branch |
| `falseLabel` | No | Custom label for the false branch |

## Wiring Rules

- Decision nodes produce exactly **two** outgoing edges: one from `true`, one from `false`
- Both branches must lead to a downstream node (no dangling branches)
- Each branch typically ends at its own End node or merges back into a shared path

## Outputs

A Decision node is **routing-only** — it has no `.output` object for downstream nodes to read. `$vars.checkTemperature.output.<field>` resolves to `undefined` and crashes the node that dereferences it. When branches merge back into a shared node, that node must **recompute the condition** from the same upstream `$vars` the Decision tested (or a per-branch node must set a variable before the merge); it cannot ask the gateway which branch ran. See [node-output-wiring.md § Routing Nodes](../../../shared/node-output-wiring.md#routing-nodes-decision--switch-have-no-output).
