# Agent Task — Planning

Runs a published **AI agent** — an LLM-based process capable of reasoning and decision-making.

## When to Use

| Situation | Use agent? |
|---|---|
| Run a published AI/LLM-based agent | Yes |
| Run a deterministic orchestration process | No — use [process](../process/planning.md) |
| Invoke an AI agent hosted on an external platform | No — use [external-agent](../external-agent/planning.md) |
| Run desktop/browser automation | No — use [rpa](../rpa/planning.md) |

## What You Need

- Agent name and folder path from registry search
- Input variable names and types (if any)
- Output variable names to capture (if any)

## Discovery

```bash
uip case registry search "<agent name>" --output json
```

Look for entries with `resource: "process"` and `resourceSubType: "Agent"`.
