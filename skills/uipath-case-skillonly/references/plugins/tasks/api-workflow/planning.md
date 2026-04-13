# API Workflow Task — Planning

Runs a published **API workflow** — a backend process that exposes a REST API interface.

## When to Use

| Situation | Use api-workflow? |
|---|---|
| Run a published API workflow for backend processing | Yes |
| Call an external third-party API directly | No — use [execute-connector-activity](../execute-connector-activity/planning.md) or a process wrapping an HTTP call |
| Run UI automation | No — use [rpa](../rpa/planning.md) |
| Run AI/LLM processing | No — use [agent](../agent/planning.md) |

## What You Need

- API Workflow name and folder path from registry search
- Input parameter names and types (if any)
- Output variable names to capture (if any)

## Discovery

```bash
uip case registry search "<workflow name>" --output json
```

Look for entries with `resource: "process"` and `resourceSubType: "Api"`.
