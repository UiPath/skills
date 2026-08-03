# Creating Eval Items for Runtime Evals

Build eval item JSON for use with `uip or eval run-offline-evals --items`.

Runtime evals against published Orchestrator packages require items in the API wire format. This guide covers how to create them. For local agent evals, see [evaluation-sets.md](evaluation-sets.md) instead.

## Item Wire Format

Each item in the `--items` JSON array represents a single test case:

```json
{
  "id": "<uuid>",
  "name": "<test-case-name>",
  "inputs": { ... },
  "expectedOutput": { ... },
  "expectedBehavior": ""
}
```

**Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique UUID for this item |
| `name` | Yes | Human-readable test case name |
| `inputs` | Yes | JSON object matching the agent's input schema |
| `expectedOutput` | No | Expected output for output-based evaluators (semantic similarity, exact match, JSON similarity) |
| `expectedBehavior` | No | Natural language description of expected behavior for trajectory evaluators |

## Simple Item Examples

### Text input agent

```json
[
  {
    "id": "7b2e9f48-c3a1-4d85-b6f2-1e8c5a9d3b70",
    "name": "Greeting test",
    "inputs": { "input": "Hello, what can you do?" },
    "expectedOutput": { "content": "I can help you with various tasks." },
    "expectedBehavior": ""
  }
]
```

### Structured input agent

```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "name": "Invoice lookup",
    "inputs": {
      "orderId": "ORD-12345",
      "customerEmail": "user@example.com"
    },
    "expectedOutput": {
      "total": 142.50,
      "status": "paid"
    },
    "expectedBehavior": ""
  }
]
```

## Items for Different Evaluator Types

### For Semantic Similarity (type 5)

Provide `expectedOutput`. The evaluator compares this against the agent's actual output using an LLM.

```json
{
  "id": "<uuid>",
  "name": "Summary test",
  "inputs": { "input": "Summarize the Q3 report" },
  "expectedOutput": { "content": "Q3 revenue grew 15% year-over-year..." },
  "expectedBehavior": ""
}
```

### For Exact Match (type 1)

Provide `expectedOutput` with the exact value the agent should return.

```json
{
  "id": "<uuid>",
  "name": "Calculator test",
  "inputs": { "input": "What is 5 + 3?" },
  "expectedOutput": { "content": "8" },
  "expectedBehavior": ""
}
```

### For Trajectory (type 7)

Provide `expectedBehavior` describing the reasoning path the agent should follow. `expectedOutput` is optional.

```json
{
  "id": "<uuid>",
  "name": "Multi-step lookup",
  "inputs": { "input": "Find the weather in NYC and recommend clothing" },
  "expectedOutput": {},
  "expectedBehavior": "Agent should call the weather API tool with location 'NYC', then analyze the temperature and conditions, then suggest appropriate clothing."
}
```

### For Both Output and Trajectory

Provide both `expectedOutput` and `expectedBehavior` when using semantic similarity and trajectory evaluators together.

```json
{
  "id": "<uuid>",
  "name": "Full evaluation",
  "inputs": { "input": "What's the weather in NYC?" },
  "expectedOutput": { "content": "It's currently 72F and sunny in New York City." },
  "expectedBehavior": "Agent calls the weather tool with location 'NYC' and returns a one-sentence summary."
}
```

## Building a Complete --items Array

```bash
uip or eval run-offline-evals \
  --process-key "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09" \
  --items '[
    {
      "id": "item-001",
      "name": "Happy path - greeting",
      "inputs": {"input": "Hello"},
      "expectedOutput": {"content": "Hello! How can I help you today?"},
      "expectedBehavior": "Agent responds with a friendly greeting."
    },
    {
      "id": "item-002",
      "name": "Edge case - empty input",
      "inputs": {"input": ""},
      "expectedOutput": {"content": "Please provide a question or request."},
      "expectedBehavior": "Agent asks for clarification when input is empty."
    },
    {
      "id": "item-003",
      "name": "Tool use - weather",
      "inputs": {"input": "What is the weather in London?"},
      "expectedOutput": {},
      "expectedBehavior": "Agent calls the weather API with location London and returns a summary."
    }
  ]' \
  --evaluators '[...]' \
  --output json
```

## Designing Good Test Cases

### Coverage patterns

| Category | Example items |
|---|---|
| Happy path | Standard inputs the agent should handle well |
| Edge cases | Empty input, very long input, special characters |
| Tool usage | Inputs that require specific tool calls |
| Error handling | Invalid requests the agent should reject gracefully |
| Multi-turn context | Inputs that test conversation state (if applicable) |

### Guidelines

- **Match the agent's input schema.** The `inputs` keys must match what the published package expects. Check with `uip or processes list` or the agent's `entry-points.json`.
- **Write specific `expectedBehavior` for trajectory evaluators.** Vague descriptions like "agent should work correctly" give meaningless scores. Describe the exact tool calls and reasoning steps.
- **Keep `expectedOutput` realistic.** For semantic similarity, minor wording differences are fine. For exact match, the output must be verbatim.
- **Use unique IDs.** Each item needs a distinct `id` to track results.

## Anti-patterns

- **Don't leave both `expectedOutput` and `expectedBehavior` empty.** At least one must be populated for evaluators to have something to score against.
- **Don't use `expectedAgentBehavior` as the field name.** The wire format uses `expectedBehavior`. The legacy field name `expectedAgentBehavior` is not accepted.
- **Don't pass inputs that don't match the agent's schema.** The runtime will fail or ignore unknown keys.
