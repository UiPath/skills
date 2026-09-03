# Evaluators

Evaluators define how agent output is scored. Each evaluator is a JSON file in `evals/evaluators/`.

## Supported evaluator types

Low-code agents support exactly these four types; all are available in Studio Web → Evaluators → **Create New** → **Add evaluator**:

| UI label | `type` | `category` | `--type` flag | Scores | LLM-based |
|---|---:|---:|---|---|---|
| LLM-as-a-judge: Semantic Similarity | 5 | 1 (`LlmAsAJudge`) | `semantic-similarity` | Whether actual and expected output have the same meaning | Yes |
| Trajectory | 7 | 3 (`Trajectory`) | `trajectory` | Whether reasoning and tool usage match expected behavior | Yes |
| Exact match | 1 | 0 (`Deterministic`) | — | Whether output precisely matches expected output | No |
| JSON similarity | 6 | 0 (`Deterministic`) | — | Whether JSON structures or values are sufficiently similar | No |

Use the UI for any type. Use the CLI only for `semantic-similarity` and `trajectory`; create Exact match and JSON similarity in the UI or by hand-writing JSON. For hand-written files, run `uip agent refresh --output json`, then run `uip agent validate --output json`; reference the evaluator’s `id` from the eval set’s `evaluatorRefs`.

The coded eval reference ([coded/lifecycle/evaluations/evaluators.md](../../coded/lifecycle/evaluations/evaluators.md)) lists 13 types, but low-code uses the legacy hierarchy (`BaseLegacyEvaluator`, with no eval-set `version` field). Its four classes are `LegacyLlmAsAJudgeEvaluator`, `LegacyTrajectoryEvaluator`, `LegacyExactMatchEvaluator`, and `LegacyJsonSimilarityEvaluator`. Coded agents use `BaseEvaluator`, eval sets with `version: "1.0"`, and distinct `evaluatorTypeId` implementations. Do not use coded-only types on low-code agents.

## JSON shapes

Filenames may be descriptive; runtime resolution uses `id` and `evaluatorRefs`. CLI-created files use `evaluator-<uuid8>.json`, where `<uuid8>` is the first 8 hex characters of the UUID. Hand-written files may use any filename.

### Exact match (`type` 1, `category` 0)

```json
{
  "fileName": "legacy-equality.json",
  "id": "<generate-uuid>",
  "name": "Equality Evaluator",
  "description": "An evaluator that judges the agent based on expected output.",
  "category": 0,
  "type": 1,
  "targetOutputKey": "*",
  "createdAt": "<iso-timestamp>",
  "updatedAt": "<iso-timestamp>"
}
```

Do not add `prompt` or `model`; deterministic evaluators bypass LLM checks.

### JSON similarity (`type` 6, `category` 0)

```json
{
  "fileName": "legacy-json-similarity.json",
  "id": "<generate-uuid>",
  "name": "JSON Similarity Evaluator",
  "description": "An evaluator that compares JSON structures with tolerance for numeric and string differences.",
  "category": 0,
  "type": 6,
  "targetOutputKey": "*",
  "createdAt": "<iso-timestamp>",
  "updatedAt": "<iso-timestamp>"
}
```

### Semantic Similarity (`type` 5, `category` 1)

```json
{
  "fileName": "legacy-llm-as-a-judge.json",
  "id": "<generate-uuid>",
  "name": "LLM As A Judge Evaluator",
  "description": "An evaluator that uses an LLM to judge the similarity of the actual output to the expected output",
  "category": 1,
  "type": 5,
  "prompt": "As an expert evaluator, analyze the semantic similarity of these outputs to determine a score from 0-100.\n----\nExpectedOutput:\n{{ExpectedOutput}}\n----\nActualOutput:\n{{ActualOutput}}\n",
  "targetOutputKey": "*",
  "model": "gpt-4.1-2025-04-14",
  "createdAt": "<iso-timestamp>",
  "updatedAt": "<iso-timestamp>"
}
```

### Trajectory (`type` 7, `category` 3)

```json
{
  "fileName": "legacy-trajectory.json",
  "id": "<generate-uuid>",
  "name": "Trajectory Evaluator",
  "description": "An evaluator that analyzes the execution trajectory and decision sequence taken by the agent.",
  "category": 3,
  "type": 7,
  "prompt": "Evaluate the agent's execution trajectory based on the expected behavior.\n\nExpected Agent Behavior: {{ExpectedAgentBehavior}}\nAgent Run History: {{AgentRunHistory}}\n\nProvide a score from 0-100 based on how well the agent followed the expected trajectory.",
  "model": "gpt-4.1-2025-04-14",
  "targetOutputKey": "*",
  "createdAt": "<iso-timestamp>",
  "updatedAt": "<iso-timestamp>"
}
```

After hand-writing an evaluator, run `uip agent refresh --output json`, then run `uip agent validate --output json`. Fix `id` collisions, missing required fields, and non-ISO-8601 timestamps before referencing the evaluator’s `id` in `evaluatorRefs`.

## Coded-only evaluators

Do not use these on low-code agents:

`uipath-contains`, `uipath-llm-judge-output-strict-json-similarity`, `uipath-llm-judge-trajectory-simulation`, `uipath-binary-classification`, `uipath-multiclass-classification`, `uipath-tool-call-order`, `uipath-tool-call-args`, `uipath-tool-call-count`, `uipath-tool-call-output`.

Switch to a coded agent (`version: "1.0"` eval sets) when one is required.

## CLI management

### Add

```bash
uip agent eval evaluator add <name> --type <type> --path <agent_dir> --output json
```

`--type` is required and accepts only `semantic-similarity` or `trajectory`. Optional flags are `--description <desc>`, `--prompt <prompt>`, `--target-key <key>`, and `--path <path>` (default `.`). The default target key is `*`; prompts use the built-in default unless overridden.

```bash
uip agent eval evaluator add content-quality \
  --type semantic-similarity \
  --path ./my-agent \
  --output json
```

### List

```bash
uip agent eval evaluator list --path <agent_dir> --output json
```

### Remove

```bash
uip agent eval evaluator remove <id_or_name> --path <agent_dir> --output json
```

Use this command rather than deleting a file by hand; it removes references from all eval sets.

## Defaults and filenames

`uip agent init` creates:

- `evaluator-default.json`, named `Default Evaluator`: semantic similarity using `{{ExpectedOutput}}` and `{{ActualOutput}}`.
- `evaluator-default-trajectory.json`, named `Default Trajectory Evaluator`: trajectory scoring using `{{UserOrSyntheticInput}}`, `{{SimulationInstructions}}`, `{{ExpectedAgentBehavior}}`, and `{{AgentRunHistory}}`.

Both default evaluators use `"model": "same-as-agent"`, which resolves to the agent’s configured model. Use an explicit model only when scoring with a different model. The runtime DTO normalizes scores to 0–100, but prompts can ask for different scales; use one scale per eval set.

CLI-added files use `evaluator-<uuid8>.json`; the `<name>` argument populates the JSON `name`, not the filename. Eval sets reference evaluator UUIDs through `id`, never filename or name.

## Evaluator JSON and mappings

```json
{
  "fileName": "evaluator-b47e26ca.json",
  "id": "b47e26ca-7a13-4c83-9ee4-039d6415fb63",
  "name": "content-quality",
  "description": "Semantic Similarity",
  "category": 1,
  "type": 5,
  "prompt": "As an expert evaluator, ... {{ExpectedOutput}} ... {{ActualOutput}} ...",
  "model": "same-as-agent",
  "targetOutputKey": "*",
  "createdAt": "2026-05-04T00:00:00.000Z",
  "updatedAt": "2026-05-04T00:00:00.000Z"
}
```

| CLI type | `type` | `category` |
|---|---:|---:|
| `semantic-similarity` | 5 | 1 (output-based) |
| `trajectory` | 7 | 3 (trajectory-based) |

## Prompts and template variables

| Type | `evaluator add` default | `uip agent init` default |
|---|---|---|
| `semantic-similarity` | Asks 0–1; uses `{{ExpectedOutput}}`, `{{ActualOutput}}` | Asks 0–100; same placeholders |
| `trajectory` | Asks 0–1; uses `{{AgentRunHistory}}`, `{{ExpectedBehavior}}` | Asks 0–100; uses `{{UserOrSyntheticInput}}`, `{{SimulationInstructions}}`, `{{ExpectedAgentBehavior}}`, `{{AgentRunHistory}}` |

When editing a prompt, retain the placeholder names already present; do not mix `{{ExpectedBehavior}}` with `{{ExpectedAgentBehavior}}`. The runtime normalizes results to 0–100, but LLM judges return the scale requested by the prompt. Rewrite inconsistent prompts so each eval set uses one scale.

Override prompts with `--prompt` and use only placeholders listed for that evaluator type; unknown placeholders are passed literally to the LLM.

```bash
uip agent eval evaluator add strict-match \
  --type semantic-similarity \
  --prompt 'Score 0-100 how closely {{ActualOutput}} matches {{ExpectedOutput}}. Return JSON {"score": N, "reason": "..."}.' \
  --path ./my-agent --output json
```

## Validation

Run `uip agent validate`; schema migration checks every file in `evals/evaluators/`.

Required fields are `fileName`, `id`, `name`, `description`, `category`, `type`, `targetOutputKey`, `createdAt`, and `updatedAt`. LLM evaluators additionally require `prompt` and `model`.

| Category | Name | Allowed `type` | Additional requirements |
|---:|---|---|---|
| 0 | Deterministic | 1, 6 | — |
| 1 | LlmAsAJudge | 5 | `prompt` and `model` |
| 3 | Trajectory | 7 | `prompt` and `model` |

Category 2 (`AgentScorer`) exists in the SDK enum but is reserved/unused; do not write it manually. Eval sets are validated against a Zod schema. Fix the reported file path, JSON path, and message, then run validate again.

## Runtime errors

These occur only after `uip agent eval run start`; `uip agent validate` does not catch them. They come from `python-eval-worker/workflows/eval/activities.py` and the SDK’s `EvaluatorFactory`.

| Error | Trigger | Fix |
|---|---|---|
| `Evaluator '<id>' is an LLM-based evaluator but 'model' is not set in its evaluatorConfig. Specify a valid model name (e.g. 'claude-haiku-4-5-20251001').` | LLM evaluator has empty or missing `model` and is not `same-as-agent`; the worker fails before the LLM gateway call. | Set a tenant-available model or set `"model": "same-as-agent"` and configure `agent.json`. |
| `'same-as-agent' model option requires agent settings. Ensure agent.json contains valid model settings.` | `same-as-agent` cannot resolve a model from `agent.json`. | Set a model in `agent.json` or use an explicit evaluator model. |

Before upload, run:

```bash
uip agent eval evaluator list --path ./my-agent --output json --output-filter '[?model==`""` || model==null]'
```

This finds LLM evaluators without an explicit model. To flag evaluators depending on `agent.json`, run:

```bash
uip agent eval evaluator list --path ./my-agent --output json --output-filter '[?model==`"same-as-agent"`]'
```

## Anti-patterns

- Do not reference evaluators by filename; use UUID `id`.
- Do not pass `--type` in PascalCase; use only `semantic-similarity` or `trajectory`.
- Do not assume `evaluator add` mirrors `init`; inspect the generated JSON, especially trajectory placeholders and score scales.
- Do not delete evaluator files by hand; run `uip agent eval evaluator remove` to clean `evaluatorRefs`.
- Do not copy evaluator JSON across projects without regenerating UUIDs; `id` collisions silently corrupt cross-project resolution.
- Do not use coded-only evaluator types on low-code agents; those without legacy classes will not load in the eval worker.
- Do not hand-write category/type combinations outside the validation matrix: category 0 → types {1, 6}; category 1 → type {5}; category 3 → type {7}.
