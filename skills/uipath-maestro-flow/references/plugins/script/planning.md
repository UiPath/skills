# Script Node — Planning

## Node Type

`core.action.script`

## When to Use

Use a Script node for custom logic, data transformation, computation, or formatting that does not require an external call.

### Selection Heuristics

| Situation | Use Script? |
| --- | --- |
| Custom logic, string manipulation, computation | Yes |
| Standard map/filter/group-by on a collection | No — use [Transform](../transform/planning.md) |
| Ambiguous input that needs reasoning or judgment | No — use [Agent](../agent/planning.md) |
| Calling an external API | No — use [HTTP](../http/planning.md) or [Connector Activity](../connector/planning.md) |
| Natural language generation | No — use [Agent](../agent/planning.md) |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `success` |

## Output Variables

- `$vars.{nodeId}.output` — the return value (must be an object)
- `$vars.{nodeId}.error` — error object if the script fails

## Key Constraints

- JavaScript only (ES2020 via Jint) — not TypeScript, not Python
- Must `return` an object: `return { key: value }` (not a bare scalar)
- No browser/DOM APIs (`fetch`, `document`, `window`, `setTimeout` are unavailable)
- Cannot make HTTP calls or access external systems
- 30-second execution timeout
- `$vars` is available as a global
