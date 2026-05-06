# Eval Sets and Data Points

An eval set is a JSON file that bundles test cases (data points) with the evaluators that score them. Each Flow project can have multiple eval sets — typically one per scenario (smoke, regression, edge cases).

## Eval Set Lifecycle

```bash
# Create
uip maestro flow eval set add "<set_name>" \
  [--evaluators <ref1>,<ref2>] \
  [--entry-point <node_id>] \
  --path <flow_project> --output json

# List
uip maestro flow eval set list --path <flow_project> --output json

# Remove
uip maestro flow eval set remove "<id_or_name>" --path <flow_project> --output json
```

### `--evaluators`

Comma-separated list of evaluator IDs or file base names. When omitted, the new eval set links to **all evaluators** present in the project at creation time. Subsequent evaluators added to the project do NOT auto-attach — link them by re-running `set add` with explicit refs, or hand-edit the eval set's `evaluatorRefs` array.

### `--entry-point`

Stored as `selectedEntrypoint` on the eval set. Accepts either:

- A flow path: `/Main.bpmn#start`
- A start node ID: `start_a1b2c3d4`

The eval set's entry point is used by `eval run start` unless `--entry-point` is overridden at run time. Pin one explicitly when the flow has multiple entry points; otherwise the first start node found is used and may not be the one you intend.

## Data Point Lifecycle

Data points (test cases) live **inline** inside the eval set JSON, not as separate files. CRUD via `uip maestro flow eval add/list/remove`:

```bash
# Add a data point
uip maestro flow eval add "<data_point_name>" \
  --set "<set_name>" \
  --inputs '{"...":"..."}' \
  [--expected '{"...":"..."}'] \
  [--criteria '{"<evaluator_id>": {...}}'] \
  [--input-file <key>=<path>] \
  [--search-text "<text>"] \
  --path <flow_project> --output json

# List
uip maestro flow eval list --set "<set_name>" --path <flow_project> --output json

# Remove
uip maestro flow eval remove "<id_or_name>" --set "<set_name>" --path <flow_project> --output json
```

### `--inputs`

JSON object whose keys must match the flow's input schema (i.e., the inputs declared on the entry node). Mismatched keys do not block `add` (the CLI stores JSON verbatim) but the run will fail when the runtime invokes the flow with the unknown keys. Validate the inputs against the flow's expected shape before running.

### `--expected`

JSON object representing the expected output. How it is consumed depends on the evaluator type:

| Evaluator type | Reads `--expected` how |
|----------------|-----------------------|
| `exact-match` | Compares the output against `expected` verbatim (or `expected[targetKey]` if `--target-key` is set on the evaluator) |
| `json-similarity` | Tree-compared with tolerance |
| `contains` | Not used directly — see `--search-text` |
| `llm-judge-output` | Substituted into `{{ExpectedOutput}}` |
| `llm-judge-strict-json` | Substituted per-key into `{{ExpectedOutput}}` |
| `llm-judge-trajectory` | Used along with `--expected-agent-behavior` (set via `--criteria`) |
| `llm-judge-trajectory-simulation` | Same as `trajectory` plus simulation context |

### `--criteria`

Per-evaluator overrides keyed by evaluator ID. Use this when one eval set contains multiple evaluators and you want each to score against different criteria for the same data point. Most common shape:

```json
{
  "<evaluator_uuid_for_trajectory>": {
    "expectedAgentBehavior": "Agent calls the weather tool with the user's location, then returns a one-sentence summary."
  },
  "<evaluator_uuid_for_output>": {
    "expectedOutput": {"summary": "Sunny in NYC, 72°F"}
  }
}
```

If `--criteria` is omitted, evaluators fall back to `--expected` (for output evaluators) and to defaults (for trajectory evaluators). Always pass an explicit `expectedAgentBehavior` for trajectory evaluators — the LLM's score against an empty `{{ExpectedAgentBehavior}}` is meaningless.

### `--input-file <key>=<path>`

Repeatable. Attach a file as input under the given key. The CLI stages the file alongside the eval set so the runtime can read it during evaluation. Useful when the flow accepts file inputs (PDFs, CSVs, images) rather than JSON only.

```bash
uip maestro flow eval add invoice-test \
  --set "Smoke Tests" \
  --inputs '{"orderId":"ORD-123"}' \
  --input-file invoice=./fixtures/invoice-123.pdf \
  --input-file receipt=./fixtures/receipt-123.png \
  --expected '{"total": 142.50}' \
  --path ./MySolution/MyFlow --output json
```

The file content is referenced from the eval set; do not delete the source file before the run completes.

### `--search-text`

Convenience flag for `contains` evaluators only. Attaches the search string to the data point so the contains evaluator knows what substring to test for. Equivalent to writing `criteria` for the contains evaluator.

```bash
uip maestro flow eval add success-keyword \
  --set "Smoke Tests" \
  --inputs '{"task":"deploy"}' \
  --search-text "deployment succeeded" \
  --path ./MySolution/MyFlow --output json
```

## Eval Set JSON Shape

A typical eval set JSON file (created by `set add`):

```json
{
  "id": "<uuid>",
  "name": "Smoke Tests",
  "version": "1.0",
  "evaluatorRefs": ["<evaluator-uuid-1>", "<evaluator-uuid-2>"],
  "selectedEntrypoint": "/Main.bpmn#start",
  "evaluations": [
    {
      "id": "<uuid>",
      "name": "hello-test",
      "inputs": {"message": "hello"},
      "expectedOutput": {"reply": "Hello! How can I help you?"},
      "evaluationCriterias": {
        "<evaluator-uuid-2>": {
          "expectedAgentBehavior": "Agent responds with a friendly greeting."
        }
      }
    }
  ]
}
```

Key fields:

- `version: "1.0"` distinguishes the new eval format from any legacy variants. Keep this.
- `evaluatorRefs` references evaluators by UUID. Filename is NOT the reference.
- `selectedEntrypoint` is the eval set's pinned entry point. Override per-run with `eval run start --entry-point`.
- `evaluations[]` is the inline list of data points. Order is informational, not significant.
- `evaluationCriterias` (note plural) is the per-data-point per-evaluator override map.

## Aligning Inputs with the Flow Schema

The data point's `inputs` JSON must match the flow's input schema at the chosen entry point. Mismatch produces runtime errors that look like missing-key or type errors after the run starts. Two ways to verify before running:

1. Inspect `<flow>.flow` in the project for the entry node's input fields.
2. Run a small smoke run against a single data point first; address any schema errors before adding more.

## Anti-patterns

- **Don't hand-write `id` UUIDs on data points.** Use `uip maestro flow eval add` so the CLI generates fresh UUIDs and keeps `evalSetId` consistent with the parent set.
- **Don't pass `--inputs` keys that aren't in the flow's input schema.** The runtime rejects unknown keys at invocation time.
- **Don't set `--expected '{}'` and skip `--criteria` for trajectory evaluators.** Both placeholders end up empty; scoring is meaningless.
- **Don't delete attached input files before the run completes.** The CLI references them by path until upload to Studio Web finishes.
- **Don't expect `--evaluators` on `set add` to auto-update.** Adding new evaluators later does not retroactively link them to existing eval sets.
