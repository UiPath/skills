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
| `display-name` | sdd.md (optional at the T-entry; required in output) | Defaults to auto-generated `Trigger N` where `N = existingTriggerCount + 1`. Because `cases add` seeds `trigger_1`, the first secondary trigger defaults to `"Trigger 2"`. |
| `description` | sdd.md (optional at the T-entry; **required in output**) | Always emitted. If sdd.md omits it, the LLM infers a natural-language description from the surrounding context (e.g., trigger's role in the sdd flow diagram or narrative). |

Position is NOT a T-entry input. It is auto-computed at execution time following the same stateful pattern as stages — see `impl-json.md` for the formula.

## Registry Resolution

**None.** Manual triggers have no registry representation.

## tasks.md Entry Format

```markdown
## T02: Configure manual trigger "Start Manually"
- display-name: "Start Manually"
- description: "Operator kicks off a case from the portal"
- order: after T01
- verify: Confirm node appended to caseplan.json.nodes and matching entry appended to entry-points.json.entryPoints; capture TriggerId
```

Both `display-name` and `description` are carried through to execution. `description` is always emitted into `caseplan.json.nodes[].data.description` (deliberate divergence from CLI which emits conditionally — the LLM ensures the key is present on every skill run so downstream tooling can rely on it).
