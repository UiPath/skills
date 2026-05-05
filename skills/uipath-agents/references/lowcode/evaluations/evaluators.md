# Evaluators

Evaluators define how agent output is scored. Each evaluator is a JSON file in `evals/evaluators/`.

## Why fewer evaluators than coded?

The coded eval reference ([coded/lifecycle/evaluations/evaluators.md](../../coded/lifecycle/evaluations/evaluators.md)) lists 13 evaluator types. Low-code lists only 4 because the two surfaces use **different engines** in the SDK:

- **Coded** uses the new evaluator hierarchy (`BaseEvaluator`, eval sets carry `version: "1.0"`). 13 distinct `evaluatorTypeId` strings, each with its own implementation class.
- **Low-code** uses the **legacy** evaluator hierarchy (`BaseLegacyEvaluator`, no `version` field on the eval set). Only 4 implementation classes ship: `LegacyLlmAsAJudgeEvaluator`, `LegacyTrajectoryEvaluator`, `LegacyExactMatchEvaluator`, `LegacyJsonSimilarityEvaluator`.

Most coded evaluator types (`contains`, `binary-classification`, `multiclass-classification`, all four `tool-call-*`, `llm-judge-output-strict-json-similarity`, `llm-judge-trajectory-simulation`) **have no legacy counterpart** and cannot be used on a low-code agent — the cloud eval worker will not load them.

The CLI also narrows the runtime surface further: of the 6 legacy `type` values the runtime accepts, the `--type` flag exposes only 4. See § Runtime-supported types not exposed by the CLI below.

## Evaluator Types (CLI-exposed)

| Type | CLI Flag | What It Scores |
|------|----------|----------------|
| Semantic Similarity | `semantic-similarity` | Whether the agent's output has the same meaning as the expected output |
| Trajectory | `trajectory` | Whether the agent's reasoning path and tool usage match expected behavior |
| Context Precision | `context-precision` | Whether retrieved context is relevant to the user's query |
| Faithfulness | `faithfulness` | Whether the agent's output is grounded in the provided context |

## Runtime-supported types not exposed by the CLI

The eval worker's discriminator (`uipath/eval/evaluators/evaluator.py` § `legacy_evaluator_discriminator`) accepts two more `type` values that have no `--type` flag. To use them, hand-write the evaluator JSON in `evals/evaluators/<filename>.json`:

### `Equals` (type 1, category 0 — Deterministic)

Exact-match comparison; no LLM. Equivalent of coded `uipath-exact-match`.

```json
{
  "fileName": "evaluator-equals.json",
  "id": "<generate-uuid>",
  "name": "exact-match",
  "description": "Exact-match evaluator",
  "category": 0,
  "type": 1,
  "targetOutputKey": "*",
  "createdAt": "<iso-timestamp>",
  "updatedAt": "<iso-timestamp>"
}
```

No `prompt`/`model` required (Deterministic category bypasses the LLM checks).

### `JsonSimilarity` (type 6, category 0 — Deterministic)

Tree-based JSON comparison; no LLM. Equivalent of coded `uipath-json-similarity`.

```json
{
  "fileName": "evaluator-json-sim.json",
  "id": "<generate-uuid>",
  "name": "json-similarity",
  "description": "JSON similarity evaluator",
  "category": 0,
  "type": 6,
  "targetOutputKey": "*",
  "createdAt": "<iso-timestamp>",
  "updatedAt": "<iso-timestamp>"
}
```

After hand-writing, run `uip agent validate --output json` to confirm the file passes schema migration. Then reference the new evaluator's `id` from your eval set's `evaluatorRefs`. Watch for: `id` collisions with existing evaluators, missing required fields, and ISO-8601 formatting on the timestamps.

## Coded-only evaluators (NOT available on low-code)

The following coded `evaluatorTypeId` strings have no legacy class — agents working on a low-code agent should not attempt to use them. Switch to a coded agent (`version: "1.0"` eval sets) if you need any of these:

`uipath-contains`, `uipath-llm-judge-output-strict-json-similarity`, `uipath-llm-judge-trajectory-simulation`, `uipath-binary-classification`, `uipath-multiclass-classification`, `uipath-tool-call-order`, `uipath-tool-call-args`, `uipath-tool-call-count`, `uipath-tool-call-output`.

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

### Semantic Similarity (`evaluator-default.json`, `name: "Default Evaluator"`)

Compares expected vs actual output for semantic equivalence. Default prompt asks the LLM for a 0–100 score and substitutes `{{ExpectedOutput}}` and `{{ActualOutput}}`.

### Trajectory (`evaluator-default-trajectory.json`, `name: "Default Trajectory Evaluator"`)

Evaluates the agent's reasoning path against expected behavior. Default prompt asks the LLM for a 0–100 score and substitutes `{{UserOrSyntheticInput}}`, `{{SimulationInstructions}}`, `{{ExpectedAgentBehavior}}`, and `{{AgentRunHistory}}`.

Both default evaluators ship with `"model": "same-as-agent"` — this is supported and resolves to the agent's configured model at runtime. Override with an explicit model only if you need to score with a different model than the agent uses.

The runtime DTO normalizes all evaluator scores to a 0–100 scale regardless of what the prompt asks for, but mixed-scale prompts in the same eval set produce confusing intermediate values — pick one scale per eval set.

## Filename vs Name

CLI-added evaluators are saved as `evaluator-<uuid8>.json` (first 8 hex chars of the evaluator UUID). The `<name>` argument populates the `name` field inside the JSON; it does NOT shape the filename.

```bash
uip agent eval evaluator add content-quality --type semantic-similarity --path ./my-agent
# Creates: evals/evaluators/evaluator-b47e26ca.json
# JSON has: "name": "content-quality"
```

The two `evaluator-default*.json` files are written by `uip agent init`, not by `evaluator add`. Eval sets reference evaluators by `id` (UUID), not by filename or name.

## Evaluator JSON Format

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

**Type and category mapping:**

| CLI Type | `type` (numeric) | `category` |
|----------|-------------------|------------|
| `semantic-similarity` | 5 | 1 (output-based) |
| `trajectory` | 7 | 3 (trajectory-based) |
| `context-precision` | 8 | 1 (output-based) |
| `faithfulness` | 9 | 1 (output-based) |

## Default Prompts and Template Variables

The prompt and score scale the CLI writes when you run `evaluator add` differs from what `uip agent init` writes for the two default evaluators:

| Type | `evaluator add` default | `uip agent init` default |
|------|-------------------------|--------------------------|
| `semantic-similarity` | Asks 0–1; uses `{{ExpectedOutput}}`, `{{ActualOutput}}` | Asks 0–100; same placeholders |
| `trajectory` | Asks 0–1; uses `{{AgentRunHistory}}`, `{{ExpectedBehavior}}` | Asks 0–100; uses `{{UserOrSyntheticInput}}`, `{{SimulationInstructions}}`, `{{ExpectedAgentBehavior}}`, `{{AgentRunHistory}}` |
| `context-precision` | Asks 0–1; uses `{{UserQuery}}`, `{{RetrievedContext}}` | Not created by `init` |
| `faithfulness` | Asks 0–1; uses `{{AgentOutput}}`, `{{Context}}` | Not created by `init` |

Two notable inconsistencies:

1. **Trajectory placeholder names**: `{{ExpectedBehavior}}` (CLI add) vs `{{ExpectedAgentBehavior}}` (init default). When editing a prompt, use the placeholders already present in that file — do not mix.
2. **Score scales**: `evaluator add` writes 0–1 prompts; `init` writes 0–100 prompts. The runtime normalizes both to 0–100 in the result DTO, but the LLM judge actually returns whatever the prompt asks for. Mixed-scale eval sets are hard to read; pick one and rewrite the prompts you don't want.

For `context-precision` and `faithfulness`, the SDK's legacy evaluator may use its own internal placeholders (`{{Query}}`, `{{Chunks}}`) that differ from what the CLI writes. Inspect the resulting evaluator JSON and run a small test before relying on customized prompts. See [evaluation-sets.md](evaluation-sets.md) § Matching evaluator to test case fields for the data flow.

## Custom Prompts

Pass `--prompt` to override the default. Use only the placeholders listed above for the chosen `--type`; unknown placeholders are passed through to the LLM as literal text.

```bash
uip agent eval evaluator add strict-match \
  --type semantic-similarity \
  --prompt 'Score 0-100 how closely {{ActualOutput}} matches {{ExpectedOutput}}. Return JSON {"score": N, "reason": "..."}.' \
  --path ./my-agent --output json
```

## What `uip agent validate` Checks

Validate runs schema migration, which enforces the following on every file in `evals/evaluators/`:

**Required fields:** `fileName`, `id`, `name`, `description`, `category`, `type`, `targetOutputKey`, `createdAt`, `updatedAt`. Missing field → `Required field "<field>" is missing`.

**Category ↔ type compatibility:**

| Category | Name | Allowed `type` | Additional requirements |
|----------|------|----------------|-------------------------|
| `0` | Deterministic | `1`, `6` | — |
| `1` | LlmAsAJudge | `5`, `8`, `9` | `prompt` and `model` required |
| `3` | Trajectory | `7` | `prompt` and `model` required |

Category `2` (`AgentScorer`) exists in the SDK enum but is reserved/unused — do not write it manually.

Eval sets are validated against a Zod schema. The CLI surfaces the offending file path, JSON path, and message — fix and re-run validate.

## Runtime Errors (Eval Worker)

These errors surface only after `uip agent eval run start` — `uip agent validate` does NOT catch them. They come from the cloud eval worker (`python-eval-worker/workflows/eval/activities.py`) and the SDK's `EvaluatorFactory`.

| Error string | Trigger | Fix |
|--------------|---------|-----|
| `Evaluator '<id>' is an LLM-based evaluator but 'model' is not set in its evaluatorConfig. Specify a valid model name (e.g. 'claude-haiku-4-5-20251001').` | Evaluator JSON has empty/missing `model` (and is not `same-as-agent`). The worker fail-fasts before calling the LLM gateway. | Set `model` in the evaluator JSON to a model available in your tenant, or set `"model": "same-as-agent"` and ensure `agent.json` has a model. |
| `'same-as-agent' model option requires agent settings. Ensure agent.json contains valid model settings.` | Evaluator uses `"same-as-agent"` but `agent.json` has no resolvable model. | Set `model` in `agent.json`, or override the evaluator with an explicit model. |

**Pre-empt locally:** before push, run

```bash
uip agent eval evaluator list --path ./my-agent --output json --output-filter '[?model==`""` || model==null]'
```

to find any LLM evaluator without an explicit model. (Switch to `--output-filter '[?model==`"same-as-agent"`]'` if you want to flag those that depend on `agent.json`.)

## Anti-patterns

- **Don't reference an evaluator by filename.** Eval sets reference evaluators by UUID (`id`).
- **Don't pass `--type` in PascalCase.** Only `semantic-similarity`, `trajectory`, `context-precision`, `faithfulness` are accepted.
- **Don't assume `evaluator add` mirrors `init`'s prompts.** They differ for trajectory; check the resulting JSON before reusing template variables in your own scoring tooling.
- **Don't delete an evaluator file by hand.** Use `uip agent eval evaluator remove` so `evaluatorRefs` in eval sets are cleaned up automatically.
- **Don't copy evaluator JSON across projects without regenerating UUIDs.** `id` collisions silently corrupt cross-project resolution.
- **Don't try to add a coded-only evaluator type to a low-code agent.** Anything starting with `uipath-tool-call-*`, `uipath-binary-classification`, `uipath-multiclass-classification`, `uipath-contains`, `uipath-llm-judge-output-strict-json-similarity`, or `uipath-llm-judge-trajectory-simulation` has no legacy class and the eval worker will not load it. If you need one of these, the agent must be coded, not low-code.
- **Don't hand-write a category/type combination outside the validate matrix.** Validate accepts cat 0 → types {1, 6}, cat 1 → types {5, 8, 9}, cat 3 → type {7}. Anything else fails schema migration.
