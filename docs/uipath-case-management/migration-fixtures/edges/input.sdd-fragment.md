# Edges Fixture — sdd Fragment

Minimal fragment exercising only the `edges` plugin. The `case` scaffold + two regular stages are prerequisites (set up in the capture script in the README).

## Flow

```
Trigger(manual) ─Start─▶ Submission Review ─Approved─▶ Approval
```

Two edges:

- `trigger_1` → `Submission Review` — **TriggerEdge**, label `Start`, default handles
- `Submission Review` → `Approval` — **Edge**, label `Approved`, default handles

Exception stages intentionally excluded — per [`plugins/edges/planning.md` § Wiring Constraints](../../../skills/uipath-case-management/references/plugins/edges/planning.md#wiring-constraints), exception stages never have edges.

## Stages (pre-created)

| Label | Kind | Purpose |
|---|---|---|
| Submission Review | regular | First stage, inbound from Trigger |
| Approval | regular | Second stage, inbound from Submission Review |
