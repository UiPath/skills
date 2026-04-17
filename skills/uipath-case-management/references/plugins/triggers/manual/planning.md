# manual trigger — Planning

A case-level trigger that the user starts by hand (e.g., clicking "Start" in the Case App). No schedule, no event — it just waits for a human.

## When to Use

Pick this plugin when the sdd.md describes the case as starting on user action:

- "User initiates the case from the portal"
- "Operator starts a new case manually"
- "Start button in the Case App"

If the sdd.md says the case runs on a schedule, use [timer](../timer/planning.md). If it starts from an external event, use [event](../event/planning.md).

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | sdd.md (optional) | Defaults to auto-generated `Trigger N` |
| `position` | rarely specified | CLI auto-positions to the left of stages |

## Registry Resolution

**None.** Manual triggers have no registry representation.

## tasks.md Entry Format

```markdown
## T02: Configure manual trigger "<display-name>"
- display-name: "Start Manually"
- order: after T01
- verify: Confirm Result: Success, capture TriggerId
```
