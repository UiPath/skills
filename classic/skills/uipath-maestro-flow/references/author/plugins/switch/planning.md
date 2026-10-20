# Switch Node — Planning

## Node Type

`core.logic.switch`

## Use When

Use a Switch node for multi-way branching with three or more paths based on ordered case expressions. Evaluate cases in order and take the first `true` case.

| Situation | Use Switch? |
| --- | --- |
| Three or more paths based on different conditions | Yes |
| Simple true/false branch | No — use [Decision](../decision/planning.md) |
| Branch on HTTP response status codes | No — use [HTTP](../http/planning.md) built-in branches |
| Branch requires reasoning on ambiguous input | No — use [Agent](../agent/planning.md) |

## Ports and Inputs

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `case-{id}` for each case, plus `default` |

| Input | Required | Description |
| --- | --- | --- |
| `cases` | Yes | Array of `{ id, label, expression }` with at least 1 item |

Each case creates the dynamic output port `case-{item.id}`. The `default` port handles unmatched values. Plan a `default` branch unless the case list provably covers every value the discriminator can hold — with nothing matched and no `default`, the instance faults `[400001]` rather than falling through.

## Wiring Rules

- Produce one outgoing edge per case, plus one from `default` unless the cases are provably exhaustive. **A discriminator read from an agent output is never exhaustive** — it is `undefined` whenever the agent returns a different shape.
- Set each case edge's `sourcePort` to `"case-{id}"`, matching the case's `id` field.
- Ensure every case branch leads to a downstream node.
