# Switch Node — Planning

## Node Type

`core.logic.switch`

## When to Use

Use a Switch node for multi-way branching (3+ paths) based on ordered case expressions. Cases are evaluated in order; the first `true` case is taken.

### Selection Heuristics

| Situation | Use Switch? |
| --- | --- |
| Three or more paths based on different conditions | Yes |
| Simple true/false branch | No — use [Decision](../decision/planning.md) |
| Branch on HTTP response status codes | No — use [HTTP](../http/planning.md) built-in branches |
| Branch requires reasoning on ambiguous input | No — use [Agent](../agent/planning.md) |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `case-{id}` (dynamic per case), `default` |

## Key Inputs

| Input | Required | Description |
| --- | --- | --- |
| `cases` | Yes | Array of `{ id, label, expression }` (min 1 item) |

Each case creates a dynamic output port: `case-{item.id}`. An optional `default` port handles unmatched cases.

## Wiring Rules

- Switch nodes produce one outgoing edge per case + optionally one from `default`
- Each case edge uses `sourcePort: "case-{id}"` where `{id}` matches the case's `id` field
- Every case branch must lead to a downstream node

## Outputs

A Switch node is **routing-only** — it has no `.output` object for downstream nodes to read. `$vars.routeByPriority.output.<field>` resolves to `undefined` and crashes the node that dereferences it. When cases merge back into a shared node, that node must **recompute the condition** from the same upstream `$vars` the Switch tested (or a per-case node must set a variable before the merge); it cannot ask the gateway which case matched. See [node-output-wiring.md § Routing Nodes](../../../shared/node-output-wiring.md#routing-nodes-decision--switch-have-no-output).
