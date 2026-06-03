# Process Task — Planning

Runs a published **agentic or orchestration process** from Orchestrator.

## When to Use

| Situation | Use process? |
|---|---|
| Run a published orchestration or agentic process | Yes |
| Run an AI/LLM-based agent | No — use [agent](../agent/planning.md) |
| Run desktop/browser automation | No — use [rpa](../rpa/planning.md) |
| Call a REST API or backend logic | No — use [api-workflow](../api-workflow/planning.md) |
| Invoke a nested case | No — use [case-management](../case-management/planning.md) |

## What You Need

- Process name and folder path from registry search
- Input variable names and types (if any)
- Output variable names to capture (if any)

## Discovery

```bash
uip case registry search "<process name>" --output json
```

Look for entries with `resource: "process"` and `resourceSubType: "ProcessOrchestration"`.
