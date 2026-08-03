# Creating Eval Sets

An eval set is the container that ties evaluators to test cases. It holds evaluator references and an inline array of items (test cases). This guide covers creating eval sets for both local agent evals and runtime evals against published Orchestrator packages.

## Local Eval Sets (uip agent eval)

Local eval sets are JSON files stored in `evals/eval-sets/`. The CLI manages them.

### Create an eval set

```bash
uip agent eval set add "Smoke Tests" --path ./my-agent --output json
```

By default, the new set references all evaluators in `evals/evaluators/`. To pick specific evaluators:

```bash
uip agent eval set add "Output Only" \
  --evaluators "a1b2c3d4-0000-0000-0000-000000000001,a1b2c3d4-0000-0000-0000-000000000002" \
  --path ./my-agent --output json
```

### Add test cases to the set

```bash
uip agent eval add "greeting-test" \
  --set "Smoke Tests" \
  --inputs '{"input": "Hello"}' \
  --expected '{"content": "Hi there! How can I help?"}' \
  --expected-agent-behavior "Agent responds with a friendly greeting" \
  --path ./my-agent --output json
```

### Add test cases with tool simulation

```bash
uip agent eval add "weather-lookup" \
  --set "Smoke Tests" \
  --inputs '{"input": "What is the weather in NYC?"}' \
  --expected '{"content": "Sunny, 72F in New York City."}' \
  --expected-agent-behavior "Agent calls the weather tool with location NYC and returns a summary" \
  --simulate-tools \
  --simulation-instructions "Return sunny weather, 72F for any location query" \
  --path ./my-agent --output json
```

### List and manage

```bash
# List eval sets
uip agent eval set list --path ./my-agent --output json

# List test cases in a set
uip agent eval list --set "Smoke Tests" --path ./my-agent --output json

# Remove a test case
uip agent eval remove "greeting-test" --set "Smoke Tests" --path ./my-agent --output json

# Remove an eval set
uip agent eval set remove "Smoke Tests" --path ./my-agent --output json
```

### Eval set JSON structure

```json
{
  "fileName": "evaluation-set-default.json",
  "id": "<uuid>",
  "name": "Smoke Tests",
  "batchSize": 10,
  "evaluatorRefs": ["<evaluator-uuid-1>", "<evaluator-uuid-2>"],
  "evaluations": [
    {
      "id": "<uuid>",
      "name": "greeting-test",
      "inputs": {"input": "Hello"},
      "expectedOutput": {"content": "Hi there!"},
      "expectedAgentBehavior": "Agent responds with a friendly greeting",
      "simulationInstructions": "",
      "simulateInput": false,
      "simulateTools": false,
      "inputGenerationInstructions": "",
      "evalSetId": "<eval-set-uuid>",
      "source": "manual",
      "createdAt": "...",
      "updatedAt": "..."
    }
  ],
  "modelSettings": [],
  "agentMemoryEnabled": false,
  "agentMemorySettings": [],
  "lineByLineEvaluation": false,
  "createdAt": "...",
  "updatedAt": "..."
}
```

Key fields:
- `evaluatorRefs` — UUIDs of evaluators to apply to all test cases
- `evaluations` — Inline array of test cases (not `testCases`)
- `batchSize` — Max concurrent test case executions
- `source` — How the test case was created (`manual` from CLI)

## Runtime Eval Sets (uip or eval run-offline-evals)

Runtime evals against published Orchestrator packages don't use local eval set files. Instead, you pass `--items` and `--evaluators` directly as JSON arrays.

### Building a complete runtime eval set

A runtime eval set is the combination of `--evaluators` + `--items` + optional `--eval-set-id`:

```bash
uip or eval run-offline-evals \
  --process-key "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09" \
  --evaluators '[
    {
      "id": "ev-001",
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
      "id": "ev-002",
      "version": "",
      "evaluatorTypeId": "7",
      "evaluatorConfig": {
        "name": "Trajectory",
        "category": 3,
        "type": 7,
        "prompt": "Evaluate the agent'\''s execution trajectory.\n\nExpected Agent Behavior: {{ExpectedAgentBehavior}}\nAgent Run History: {{AgentRunHistory}}\n\nProvide a score from 0-100.",
        "model": "gpt-4.1-2025-04-14",
        "targetOutputKey": "*"
      }
    }
  ]' \
  --items '[
    {
      "id": "item-001",
      "name": "Happy path greeting",
      "inputs": {"input": "Hello"},
      "expectedOutput": {"content": "Hi! How can I help?"},
      "expectedBehavior": "Agent responds with a friendly greeting."
    },
    {
      "id": "item-002",
      "name": "Tool usage - weather",
      "inputs": {"input": "Weather in NYC?"},
      "expectedOutput": {},
      "expectedBehavior": "Agent calls weather tool with location NYC and returns a summary."
    }
  ]' \
  --output json
```

See [creating-evaluators.md](creating-evaluators.md) for evaluator config details and [creating-eval-items.md](creating-eval-items.md) for item format details.

## Designing Eval Set Coverage

### Organize by concern

| Eval set name | What it tests | Evaluators |
|---|---|---|
| "Happy Path" | Standard inputs the agent handles well | Semantic similarity |
| "Tool Usage" | Agent calls the right tools with right args | Trajectory |
| "Error Handling" | Agent handles bad input gracefully | Semantic similarity |
| "Full Suite" | End-to-end coverage | Semantic similarity + Trajectory |

### Coverage checklist

- At least one happy-path test case per agent capability
- At least one edge case (empty input, very long input, special characters)
- At least one test case per tool the agent uses (with `--expected-agent-behavior` describing the expected tool call)
- At least one error-handling test case (invalid request, missing data)
- For multi-tool agents: test cases that require combining multiple tools

### Test case sizing

- Start small: 3-5 test cases covering the main paths
- Add more as you find regressions or edge cases
- Keep each eval set focused — one set per concern is easier to debug than one big set
- Use `--batch-size` to control concurrency (default 10 for local, 5 for runtime)

## Anti-patterns

- **Don't hand-edit `evaluatorRefs` UUIDs.** Use `uip agent eval set add --evaluators` or let the CLI default to all evaluators.
- **Don't add test cases with `--inputs` keys that don't match `entry-points.json`.** The runtime will reject them. Run `uip agent validate` to catch this early.
- **Don't leave both `expectedOutput` and `expectedAgentBehavior` empty.** Evaluators score against these — empty values give meaningless scores.
- **Don't copy eval sets across projects without regenerating UUIDs.** Evaluator UUIDs are project-specific.
- **Evaluators added after `set add` are NOT auto-linked.** Either recreate the set with `--evaluators` or add the evaluator ref manually.
