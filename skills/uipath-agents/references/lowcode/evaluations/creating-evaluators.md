# Creating Evaluators for Runtime Evals

Build evaluator config JSON for use with `uip or eval run-offline-evals --evaluators`.

Runtime evals against published Orchestrator packages require evaluators in the API wire format. This guide covers how to create them. For local agent evals, see [evaluators.md](evaluators.md) instead.

## Evaluator Wire Format

Each evaluator in the `--evaluators` JSON array must have this shape:

```json
{
  "id": "<uuid>",
  "version": "",
  "evaluatorTypeId": "<type-id-string>",
  "evaluatorConfig": {
    "name": "<evaluator-name>",
    "targetOutputKey": "*",
    ...type-specific fields...
  }
}
```

**Required fields:**
- `id` — Unique UUID for this evaluator
- `evaluatorTypeId` — One of the supported type IDs (see table below)
- `evaluatorConfig` — Type-specific config object

## Supported Evaluator Types

| Type | `evaluatorTypeId` | LLM-based | Score |
|------|-------------------|-----------|-------|
| Exact match | `1` | No | Binary (0/1) |
| Semantic similarity | `5` | Yes | 0-100 |
| JSON similarity | `6` | No | 0-1 |
| Trajectory | `7` | Yes | 0-100 |

## Evaluator Templates

### Exact Match (type 1)

Verbatim comparison of agent output against expected output.

```json
{
  "id": "<generate-uuid>",
  "version": "",
  "evaluatorTypeId": "1",
  "evaluatorConfig": {
    "name": "Exact Match",
    "description": "Compares agent output verbatim against expected output.",
    "category": 0,
    "type": 1,
    "targetOutputKey": "*"
  }
}
```

### Semantic Similarity (type 5)

LLM-based scoring of meaning equivalence between expected and actual output.

```json
{
  "id": "<generate-uuid>",
  "version": "",
  "evaluatorTypeId": "5",
  "evaluatorConfig": {
    "name": "Semantic Similarity",
    "description": "Uses an LLM to judge the similarity of outputs.",
    "category": 1,
    "type": 5,
    "prompt": "As an expert evaluator, analyze the semantic similarity of these outputs to determine a score from 0-100.\n----\nExpectedOutput:\n{{ExpectedOutput}}\n----\nActualOutput:\n{{ActualOutput}}\n",
    "model": "gpt-4.1-2025-04-14",
    "targetOutputKey": "*"
  }
}
```

**Template variables:** `{{ExpectedOutput}}`, `{{ActualOutput}}`

### JSON Similarity (type 6)

Tree-based structural comparison with tolerance for numeric and string differences.

```json
{
  "id": "<generate-uuid>",
  "version": "",
  "evaluatorTypeId": "6",
  "evaluatorConfig": {
    "name": "JSON Similarity",
    "description": "Compares JSON structures with tolerance for minor differences.",
    "category": 0,
    "type": 6,
    "targetOutputKey": "*"
  }
}
```

### Trajectory (type 7)

LLM-based scoring of the agent's reasoning path and tool usage.

```json
{
  "id": "<generate-uuid>",
  "version": "",
  "evaluatorTypeId": "7",
  "evaluatorConfig": {
    "name": "Trajectory",
    "description": "Analyzes the execution trajectory and decision sequence.",
    "category": 3,
    "type": 7,
    "prompt": "Evaluate the agent's execution trajectory based on the expected behavior.\n\nExpected Agent Behavior: {{ExpectedAgentBehavior}}\nAgent Run History: {{AgentRunHistory}}\n\nProvide a score from 0-100 based on how well the agent followed the expected trajectory.",
    "model": "gpt-4.1-2025-04-14",
    "targetOutputKey": "*"
  }
}
```

**Template variables:** `{{ExpectedAgentBehavior}}`, `{{AgentRunHistory}}`, `{{UserOrSyntheticInput}}`, `{{SimulationInstructions}}`

## Building the --evaluators Array

Combine one or more evaluators into a JSON array:

```bash
uip or eval run-offline-evals \
  --process-key "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09" \
  --items '[...]' \
  --evaluators '[
    {
      "id": "a1b2c3d4-0000-0000-0000-000000000001",
      "version": "",
      "evaluatorTypeId": "5",
      "evaluatorConfig": {
        "name": "Semantic Similarity",
        "category": 1,
        "type": 5,
        "prompt": "As an expert evaluator, analyze the semantic similarity of these outputs to determine a score from 0-100.\n----\nExpectedOutput:\n{{ExpectedOutput}}\n----\nActualOutput:\n{{ActualOutput}}\n",
        "model": "gpt-4.1-2025-04-14",
        "targetOutputKey": "*"
      }
    },
    {
      "id": "a1b2c3d4-0000-0000-0000-000000000002",
      "version": "",
      "evaluatorTypeId": "7",
      "evaluatorConfig": {
        "name": "Trajectory",
        "category": 3,
        "type": 7,
        "prompt": "Evaluate the agent'\''s execution trajectory based on the expected behavior.\n\nExpected Agent Behavior: {{ExpectedAgentBehavior}}\nAgent Run History: {{AgentRunHistory}}\n\nProvide a score from 0-100.",
        "model": "gpt-4.1-2025-04-14",
        "targetOutputKey": "*"
      }
    }
  ]' \
  --output json
```

## Choosing Evaluator Types

| Agent output | Use |
|---|---|
| Deterministic, exact values | Exact match (type 1) |
| Structured JSON responses | JSON similarity (type 6) |
| Natural language text | Semantic similarity (type 5) |
| Multi-step reasoning, tool calls | Trajectory (type 7) |
| Both output quality and reasoning path | Semantic similarity + Trajectory together |

## Anti-patterns

- **Don't use `"model": "same-as-agent"` in runtime evals.** The runtime eval has no access to `agent.json` to resolve this. Always use an explicit model ID.
- **Don't reuse UUIDs across evaluators.** Each evaluator must have a unique `id`.
- **Don't use deterministic evaluators (exact match, JSON similarity) for natural language outputs.** They will fail on paraphrases.
- **Don't omit `prompt` or `model` on LLM-based evaluators (types 5 and 7).** The API will return errors.
