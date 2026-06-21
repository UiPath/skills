# Case Management Task — Planning

Invokes a **nested case management process** — spawns a child case from within the current case.

## When to Use

| Situation | Use case-management? |
|---|---|
| A stage needs to spawn and wait for a child case | Yes |
| Hierarchical or sub-case processing patterns | Yes |
| Run a standard automation process | No — use [process](../process/planning.md) |
| Run an AI agent | No — use [agent](../agent/planning.md) |

## What You Need

- Child case process name and folder path from registry search
- Input variables to pass into the child case
- Output variables to receive from the child case

## Discovery

```bash
uip case registry search "<case name>" --output json
```

Look for entries with `resource: "process"` and `resourceSubType: "CaseManagement"`.
