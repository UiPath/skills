# Model Selection Guide

Programmatic model discovery and selection for low-code agents.

## Discover Available Models

```bash
uip agent model list --all-fields --output json
```

> **`--all-fields` is mandatory.** Without it the response omits priority and capability fields listed below — making informed model selection impossible.

## Response Fields

Response shape:

```json
{ "Result": "Success", "Code": "AgentModelList", "Data": [...] }
```

Each object in `Data[]`:

| Field | Description |
|-------|-------------|
| `name` | Model identifier — use directly as `settings.model` |
| `provider` | Hosting provider (`AwsBedrock`, `OpenAi`, `VertexAi`) |
| `isSuggested` | UiPath-recommended model |
| `isPreview` | Preview/experimental |
| `isByo` | Bring-your-own model (requires `byoModelConnectionId`) |
| `defaultPriority` | Auto-selection rank for autonomous agents (lower = higher priority, null = not candidate) |
| `defaultConversationalPriority` | Auto-selection rank for conversational agents (same semantics) |
| `maxInputTokens` | Input context window (may be null) |
| `maxTokens` | Max output tokens |

## Selection Rules

1. Prefer `isSuggested: true`
2. For platform default: use `defaultPriority` (autonomous) or `defaultConversationalPriority` (conversational) — filter to non-null, sort ascending, pick the entry with the smallest value
3. Skip `isByo: true` unless user explicitly provides a BYO connection

## Example Output

Truncated — representative entries showing suggested and default-priority patterns:

```json
{
  "Result": "Success",
  "Code": "AgentModelList",
  "Data": [
    {
      "name": "anthropic.claude-sonnet-4-6",
      "provider": "AwsBedrock",
      "isSuggested": true,
      "isPreview": false,
      "isByo": false,
      "defaultPriority": 1,
      "defaultConversationalPriority": null,
      "maxInputTokens": 200000,
      "maxTokens": 16384
    },
    {
      "name": "gpt-4.1-2025-04-14",
      "provider": "OpenAi",
      "isSuggested": true,
      "isPreview": false,
      "isByo": false,
      "defaultPriority": 2,
      "defaultConversationalPriority": 1,
      "maxInputTokens": 1047576,
      "maxTokens": 32768
    }
  ]
}
```
