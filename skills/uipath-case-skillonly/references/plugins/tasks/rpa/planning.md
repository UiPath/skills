# RPA Task — Planning

Runs a published **RPA automation** — desktop or browser workflow using UI interaction.

## When to Use

| Situation | Use rpa? |
|---|---|
| Automate a legacy desktop application with no API | Yes |
| Automate browser-based UI interaction | Yes |
| Call a REST API or structured backend | No — use [api-workflow](../api-workflow/planning.md) |
| Run AI/LLM-based processing | No — use [agent](../agent/planning.md) |
| Run an orchestration process | No — use [process](../process/planning.md) |

## What You Need

- RPA process name and folder path from registry search
- Input argument names and types (if any)
- Output argument names to capture (if any)

## Discovery

```bash
uip case registry search "<process name>" --output json
```

Look for entries with `resource: "process"` (no resourceSubType, or `resourceSubType` absent — RPA processes don't have a subtype).
