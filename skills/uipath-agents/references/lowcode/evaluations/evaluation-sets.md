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

### Aligning `--inputs` with `entry-points.json`

`--inputs` JSON keys must match the `input` schema in `entry-points.json`. Mismatched keys do not block `eval add` (the CLI stores the JSON verbatim) but will fail at run time when the Agent Runtime invokes the agent. Run `uip agent validate --output json` after adding test cases to surface schema drift.

### Matching evaluator to test case fields

The `--inputs` and `--expected` flags populate `inputs` and `expectedOutput` on the test case. Each evaluator type sources its placeholder values from a different combination of test-case fields and agent run trace:

| Evaluator Type | From test case | From agent run trace |
|----------------|---------------|----------------------|
| `semantic-similarity` | `expectedOutput` → `{{ExpectedOutput}}` | Agent output → `{{ActualOutput}}` |
| `trajectory` | `expectedAgentBehavior` → `{{ExpectedAgentBehavior}}`, `inputs` → `{{UserOrSyntheticInput}}`, `simulationInstructions` → `{{SimulationInstructions}}` | Trace → `{{AgentRunHistory}}` |
| `context-precision` | (none directly used) | RETRIEVER spans `input.value` → `{{UserQuery}}`, `output.value.documents` → `{{RetrievedContext}}` |
| `faithfulness` | `expectedOutput` → `{{AgentOutput}}` (note: it is the *expected* output that is treated as the candidate text to fact-check, not the agent's actual output) | Trace span outputs (RETRIEVER + tool calls) → `{{Context}}` |

`context-precision` and `faithfulness` are **trace-driven evaluators**. They extract `{{UserQuery}}`, `{{RetrievedContext}}`, and `{{Context}}` by walking `openinference.span.kind == "RETRIEVER"` (and other tool spans) on the agent's run trace. Their behavior:

- **The agent must perform retrieval** (Context Grounding / index / DataFabric / a tool that emits an OpenInference RETRIEVER span). Without retrieval spans, the placeholders resolve to empty and scores collapse.
- **`--inputs` and `--expected` are not consumed in the obvious way**: `context-precision` ignores test-case `inputs` (it reads the query from the trace); `faithfulness` reads the *expected* output (not the agent's actual output) as the candidate text.
- **CLI-default placeholders may differ from SDK-internal placeholders.** The CLI writes prompts with `{{UserQuery}}` and `{{RetrievedContext}}` for context-precision, but the SDK's legacy evaluator hardcodes `{{Query}}` and `{{Chunks}}` internally. Inspect the resulting evaluator JSON; if you customize the prompt, match the placeholders the runtime actually substitutes (test with a small run before relying on results).

If the agent has no retrieval step, remove `context-precision` and `faithfulness` from the eval set rather than letting them silently score everything as 0.

For trajectory evaluation, write `--expected-agent-behavior` as a natural language description of what the agent should do, not what it should output:

```bash
uip agent eval add tool-usage-test \
  --set "Default Evaluation Set" \
  --inputs '{"input":"What is the weather in NYC?"}' \
  --expected-agent-behavior "Agent should call the weather tool with location NYC and return a formatted weather summary" \
  --path ./my-agent --output json
```

### Simulation options

- `--simulate-input` — runtime generates synthetic input variations based on the provided input
- `--simulate-tools` — tool calls are simulated rather than executed against real services
- `--input-generation-instructions` — guides synthetic input generation (e.g., "generate edge cases with empty strings and special characters")
- `--simulation-instructions` — guides overall simulation behavior

Use these to expand test coverage without writing every input by hand.

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

The `source` field indicates how the test case was created. CLI-added test cases are always `"manual"` (verified). Other observed values from Studio Web include `"debugRun"`, `"runtimeRun"`, `"simulatedRun"`, and `"autopilotUserInitiated"` — treat the `source` field as an enum but do not set it manually; the CLI and Studio Web own this value.

## Anti-patterns

- **Don't hand-write `evalSetId` or test case `id` UUIDs.** Use `uip agent eval add` so the CLI keeps `evaluations[].evalSetId` consistent with the parent eval set's `id`.
- **Don't add `--inputs` keys that are not in `entry-points.json`.** The runtime will reject the test case at execution time. Run `uip agent validate` to catch this before push.
- **Don't add `context-precision` or `faithfulness` evaluators to an eval set whose agent has no RETRIEVER span.** Both extract their placeholders from agent trace spans, not from `inputs`/`expectedOutput`. No retrieval → scores collapse to 0.
- **Don't expect `faithfulness` to read the agent's actual output.** It reads `expectedOutput` (the criteria field) as the candidate text. To fact-check actual agent output, use `semantic-similarity` against an expected ground truth instead.
- **Don't set `--expected '{}'` (empty) and `--expected-agent-behavior ""` together.** The semantic-similarity evaluator scores against an empty `{{ExpectedOutput}}`; the trajectory evaluator scores against an empty `{{ExpectedAgentBehavior}}`. Every run scores low for non-actionable reasons.
- **Don't set the `source` field manually.** Owned by CLI and Studio Web; hand-edits may be overwritten on the next sync.
