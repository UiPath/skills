# Evaluators

Evaluators define how agent output is scored. Each evaluator is a JSON file in `evals/evaluators/`.

## Evaluator Types

| Type | CLI Flag | What It Scores |
|------|----------|----------------|
| Semantic Similarity | `semantic-similarity` | Whether the agent's output has the same meaning as the expected output |
| Trajectory | `trajectory` | Whether the agent's reasoning path and tool usage match expected behavior |
| Context Precision | `context-precision` | Whether retrieved context is relevant to the user's query |
| Faithfulness | `faithfulness` | Whether the agent's output is grounded in the provided context |

## Managing Evaluators

### Add an evaluator

```bash
uip agent eval evaluator add <name> --type <type> --path <agent_dir> --output json
```

**Options:**

| Flag | Required | Description | Default |
|------|----------|-------------|---------|
| `--type <type>` | Yes | One of: `semantic-similarity`, `trajectory`, `context-precision`, `faithfulness` | — |
| `--description <desc>` | No | Human-readable description | Auto-generated from type |
| `--prompt <prompt>` | No | Custom LLM evaluation prompt | Built-in default per type |
| `--target-key <key>` | No | Specific output key to evaluate | `*` (all keys) |
| `--path <path>` | No | Agent project directory | `.` |

**Example:**
```bash
uip agent eval evaluator add content-quality \
  --type semantic-similarity \
  --path ./my-agent \
  --output json
```

### List evaluators

```bash
uip agent eval evaluator list --path <agent_dir> --output json
```

### Remove an evaluator

```bash
uip agent eval evaluator remove <id_or_name> --path <agent_dir> --output json
```

Removing an evaluator automatically removes its references from all eval sets that reference it.

## Default Evaluators

`uip agent init` creates two default evaluators:

### Semantic Similarity (`evaluator-default.json`)

Compares expected vs actual output for semantic equivalence. Uses template variables `{{ExpectedOutput}}` and `{{ActualOutput}}`. Scores 0–100.

### Trajectory (`evaluator-default-trajectory.json`)

Evaluates the agent's reasoning path against expected behavior. Uses template variables `{{UserOrSyntheticInput}}`, `{{SimulationInstructions}}`, `{{ExpectedAgentBehavior}}`, and `{{AgentRunHistory}}`. Scores 0–100.

Both default evaluators use `"same-as-agent"` as the model, which resolves to the agent's configured model at runtime.

## Evaluator JSON Format

```json
{
  "fileName": "evaluator-content-quality.json",
  "id": "<uuid>",
  "name": "content-quality",
  "description": "Evaluates semantic similarity of output",
  "category": 1,
  "type": 5,
  "prompt": "Compare {{ExpectedOutput}} with {{ActualOutput}}...",
  "model": "same-as-agent",
  "targetOutputKey": "*",
  "createdAt": "2025-01-01T00:00:00.000Z",
  "updatedAt": "2025-01-01T00:00:00.000Z"
}
```

**Type and category mapping:**

| CLI Type | `type` (numeric) | `category` |
|----------|-------------------|------------|
| `semantic-similarity` | 5 | 1 (output-based) |
| `trajectory` | 7 | 3 (trajectory-based) |
| `context-precision` | 8 | 1 (output-based) |
| `faithfulness` | 9 | 1 (output-based) |

## Custom Prompts

When `--prompt` is omitted, the CLI uses a built-in default prompt for each type. To customize, pass a prompt string using the appropriate template variables:

- **Semantic Similarity**: `{{ExpectedOutput}}`, `{{ActualOutput}}`
- **Trajectory**: `{{AgentRunHistory}}`, `{{ExpectedBehavior}}`
- **Context Precision**: `{{UserQuery}}`, `{{RetrievedContext}}`
- **Faithfulness**: `{{AgentOutput}}`, `{{Context}}`
