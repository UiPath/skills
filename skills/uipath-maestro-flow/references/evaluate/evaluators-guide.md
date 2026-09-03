# Flow Evaluators Guide

The seven evaluator types for `uip maestro flow eval evaluator add --type <type>`. Flow uses the same `uipath-*` evaluator type IDs as the coded evaluator engine (NOT the legacy IDs the low-code `uipath-agents` skill uses). Each `--type` kebab-case value maps to a `uipath-*` evaluator under the hood:

| `--type` flag | Internal `evaluatorTypeId` | LLM-based | Score scale |
|---------------|---------------------------|-----------|-------------|
| `exact-match` | `uipath-exact-match` | No | Binary (0/1) |
| `json-similarity` | `uipath-json-similarity` | No | Continuous (0–1) |
| `contains` | `uipath-contains` | No | Binary (0/1) |
| `llm-judge-output` | `uipath-llm-judge-output-semantic-similarity` | Yes | Continuous (0–1) |
| `llm-judge-strict-json` | `uipath-llm-judge-output-strict-json-similarity` | Yes | Continuous (0–1) |
| `llm-judge-trajectory` | `uipath-llm-judge-trajectory-similarity` | Yes | Continuous (0–1) |
| `llm-judge-trajectory-simulation` | `uipath-llm-judge-trajectory-simulation` | Yes | Continuous (0–1) |

The four classification and tool-call evaluators (`uipath-binary-classification`, `uipath-multiclass-classification`, `uipath-tool-call-*`) that exist in the coded SDK are **not** exposed by `uip maestro flow eval evaluator add`. Use the seven listed above.

## When to Pick Each Type

| Goal | Type | Notes |
|------|------|-------|
| Strict equality of a known output value | `exact-match` | Binary; no LLM. Cheapest. Use for deterministic agents. |
| Compare structured JSON outputs with tolerance for ordering / minor diffs | `json-similarity` | Tree-based; numeric tolerance ~1%, string Levenshtein. |
| Pass/fail on whether a substring appears | `contains` | Use `--search-text` on the data point, not the evaluator. |
| Score natural-language similarity between expected and actual | `llm-judge-output` | Default LLM judge. Set `--model`. |
| Per-key strict JSON scoring with LLM judgment on differences | `llm-judge-strict-json` | LLM penalizes per-field. Use when each output key matters independently. |
| Score whether the agent's reasoning path matches expected behavior | `llm-judge-trajectory` | Reads agent run history. Use `--expected-agent-behavior` on data points. |
| As above but with simulated tool calls / inputs | `llm-judge-trajectory-simulation` | Use when the flow can't safely execute real tools during eval. |

## Adding an Evaluator (CLI)

```bash
# Deterministic — no model needed
uip maestro flow eval evaluator add exact-greeting \
  --type exact-match \
  --target-key "greeting" \
  --path ./MySolution/MyFlow --output json

# LLM-judge — model is effectively required
uip maestro flow eval evaluator add greeting-quality \
  --type llm-judge-output \
  --model gpt-4.1-2025-04-14 \
  --description "Score greeting tone and completeness" \
  --path ./MySolution/MyFlow --output json
```

Critical: pass `--model` on every `llm-judge-*` evaluator. Empty `model` triggers a 500 from the LLM gateway only after retries — unfriendly to debug.

## `--target-key`

Defaults to `*` (the entire output object). Set a specific key when only one field of the output should be scored:

- Output: `{"greeting": "Hello!", "metadata": {"latencyMs": 12}}` 
- `--target-key "greeting"` scores only the greeting string, ignoring metadata noise.
- `--target-key "*"` (default) scores the whole object.

## Evaluator JSON Shape

The CLI writes evaluator JSON files into the project's evaluator directory. Filenames follow `<name>-<suffix>.json` for CLI-created files; hand-written files can use any descriptive name. Let `eval set add` write `evaluatorRefs` instead of hand-editing them.

### Deterministic example (`exact-match`)

```json
{
  "id": "<generate-uuid>",
  "name": "exact-greeting",
  "description": "Strict greeting match",
  "version": "1.0",
  "evaluatorTypeId": "uipath-exact-match",
  "evaluatorConfig": {
    "name": "exact-greeting",
    "targetOutputKey": "greeting",
    "caseSensitive": false,
    "negated": false
  }
}
```

`exact-match`, `json-similarity`, and `contains` do NOT carry a `model` or `prompt`.

### LLM-judge example (`llm-judge-output`)

```json
{
  "id": "<generate-uuid>",
  "name": "greeting-quality",
  "description": "Score greeting tone and completeness",
  "version": "1.0",
  "evaluatorTypeId": "uipath-llm-judge-output-semantic-similarity",
  "evaluatorConfig": {
    "name": "greeting-quality",
    "model": "gpt-4.1-2025-04-14",
    "temperature": 0,
    "maxTokens": 4096,
    "targetOutputKey": "*",
    "prompt": "Score 0-1 the semantic similarity of {{ActualOutput}} vs {{ExpectedOutput}}. Return JSON {\"score\": N, \"reason\": \"...\"}."
  }
}
```

Template variables per type:

| Type | Placeholders |
|------|-------------|
| `llm-judge-output` | `{{ExpectedOutput}}`, `{{ActualOutput}}` |
| `llm-judge-strict-json` | `{{ExpectedOutput}}`, `{{ActualOutput}}` |
| `llm-judge-trajectory` | `{{AgentRunHistory}}`, `{{ExpectedAgentBehavior}}`, `{{UserOrSyntheticInput}}` |
| `llm-judge-trajectory-simulation` | `{{AgentRunHistory}}`, `{{ExpectedAgentBehavior}}`, `{{UserOrSyntheticInput}}`, `{{SimulationInstructions}}` |

When `--prompt` is omitted, the CLI inserts a built-in default for each type. Override with `--prompt` only when you need different wording or scoring criteria — keep the same placeholders.

## Custom Prompts

```bash
uip maestro flow eval evaluator add strict-match \
  --type llm-judge-output \
  --model gpt-4.1-2025-04-14 \
  --prompt 'Score 0-1 how closely {{ActualOutput}} matches {{ExpectedOutput}}. Return JSON {"score": N, "reason": "..."}.' \
  --path ./MySolution/MyFlow --output json
```

Unknown placeholders are passed through to the LLM as literal text — they are not silent errors but they will not be substituted with run data.

## Removing an Evaluator

```bash
uip maestro flow eval evaluator remove greeting-quality \
  --path ./MySolution/MyFlow --output json
```

Removing an evaluator does NOT auto-clean `evaluatorRefs` arrays in eval sets that reference it. After removing, re-list eval sets and reconcile any stale refs:

```bash
uip maestro flow eval set list --path ./MySolution/MyFlow --output json
```

## Anti-patterns

- **Don't pass `--type` in PascalCase.** `ExactMatch` fails; only `exact-match` is accepted.
- **Don't omit `--model` on `llm-judge-*`.** The cloud worker fail-fasts before calling the LLM gateway; the resulting 500 is unhelpful.
- **Don't hand-write evaluator refs unless you are repairing an eval set.** Omit `--evaluators` so the CLI links all current evaluators, or use `eval set add --evaluators <generated_id_or_file_base>`. Do not pass the evaluator display name.
- **Don't copy evaluator JSON across projects without regenerating UUIDs.** `id` collisions silently corrupt resolution.
- **Don't use deterministic evaluators (`exact-match`, `json-similarity`, `contains`) for natural-language outputs.** They will fail almost every test that paraphrases.
- **Don't mix trajectory and output evaluators on the same data point unless the data point provides both `--expected` and `--expected-agent-behavior`.** Otherwise one of them scores against an empty placeholder.
