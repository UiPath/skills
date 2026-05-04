# Evaluation Sets and Test Cases

Evaluation sets group test cases and reference which evaluators to use. Each set is a JSON file in `evals/eval-sets/`. Test cases are stored inline within the eval set.

## Managing Eval Sets

### Add an eval set

```bash
uip agent eval set add <name> --path <agent_dir> --output json
```

**Options:**

| Flag | Required | Description | Default |
|------|----------|-------------|---------|
| `--evaluators <ids>` | No | Comma-separated evaluator IDs | All existing evaluators |
| `--path <path>` | No | Agent project directory | `.` |

When `--evaluators` is not provided, the new eval set automatically references **all** evaluators in the project.

### List eval sets

```bash
uip agent eval set list --path <agent_dir> --output json
```

### Remove an eval set

```bash
uip agent eval set remove <id_or_name> --path <agent_dir> --output json
```

## Managing Test Cases

Test cases live inside eval sets. Each test case defines an input, expected output, and optional behavior expectations.

### Add a test case

```bash
uip agent eval add <name> \
  --set "<eval_set_name>" \
  --inputs '{"input":"hello"}' \
  --expected '{"content":"greeting response"}' \
  --path <agent_dir> \
  --output json
```

**Options:**

| Flag | Required | Description | Default |
|------|----------|-------------|---------|
| `--set <name>` | Yes | Eval set name or ID | — |
| `--inputs <json>` | Yes | Input values as JSON | — |
| `--expected <json>` | No | Expected output as JSON | `{}` |
| `--expected-agent-behavior <text>` | No | Description of expected behavior (used by trajectory evaluator) | `""` |
| `--simulation-instructions <text>` | No | Instructions for simulating agent behavior | `""` |
| `--simulate-input` | No | Enable input simulation | `false` |
| `--simulate-tools` | No | Enable tool simulation | `false` |
| `--input-generation-instructions <text>` | No | Instructions for generating synthetic inputs | `""` |
| `--path <path>` | No | Agent project directory | `.` |

### List test cases

```bash
uip agent eval list --set "<eval_set_name>" --path <agent_dir> --output json
```

### Remove a test case

```bash
uip agent eval remove <id_or_name> --set "<eval_set_name>" --path <agent_dir> --output json
```

## Test Case Design

### Matching evaluator to test case fields

| Evaluator Type | Key Test Case Fields |
|---------------|---------------------|
| Semantic Similarity | `--inputs`, `--expected` |
| Trajectory | `--inputs`, `--expected-agent-behavior` |
| Context Precision | `--inputs`, `--expected` |
| Faithfulness | `--inputs`, `--expected` |

For trajectory evaluation, write `--expected-agent-behavior` as a natural language description of what the agent should do, not what it should output:

```bash
uip agent eval add tool-usage-test \
  --set "Default Evaluation Set" \
  --inputs '{"input":"What is the weather in NYC?"}' \
  --expected-agent-behavior "Agent should call the weather tool with location NYC and return a formatted weather summary" \
  --path ./my-agent --output json
```

### Simulation options

- `--simulate-input` — the runtime generates synthetic input variations based on the provided input
- `--simulate-tools` — tool calls are simulated rather than executed against real services
- `--input-generation-instructions` — guides synthetic input generation (e.g., "generate edge cases with empty strings and special characters")
- `--simulation-instructions` — guides the overall simulation behavior

These are useful for expanding test coverage without writing every input by hand.

## Eval Set JSON Format

```json
{
  "fileName": "evaluation-set-default.json",
  "id": "<uuid>",
  "name": "Default Evaluation Set",
  "batchSize": 10,
  "evaluatorRefs": ["<evaluator-uuid-1>", "<evaluator-uuid-2>"],
  "evaluations": [
    {
      "id": "<uuid>",
      "name": "happy-path",
      "inputs": {"input": "hello"},
      "expectedOutput": {"content": "greeting"},
      "expectedAgentBehavior": "",
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

The `source` field indicates how the test case was created: `"manual"` (CLI), `"debugRun"` (from a debug session), `"runtimeRun"` (from a live run), `"simulatedRun"`, or `"autopilotUserInitiated"`.
