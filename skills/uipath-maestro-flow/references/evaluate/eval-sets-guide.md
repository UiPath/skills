# Eval Sets and Data Points

An eval set is a JSON file containing test cases (data points) and evaluators. A Flow project may have multiple sets, typically one per scenario.

## Eval Set Lifecycle

Run:

```bash
uip maestro flow eval set add "<set_name>" \
  [--evaluators <ref1>,<ref2>] \
  [--entry-point <node_id>] \
  --path <flow_project> --output json

uip maestro flow eval set list --path <flow_project> --output json

uip maestro flow eval set remove "<id_or_name>" --path <flow_project> --output json
```

`--evaluators` accepts comma-separated evaluator IDs or generated file base names. If omitted, the set links to all evaluators present at creation and writes generated evaluator file refs such as `greeting-match-62c0793a.json`; prefer omission when using every current evaluator. Do not pass an evaluator display name such as `greeting-match`: this writes the display name into `evaluatorRefs`, which Studio Web eval runs cannot resolve. For an explicit list, run `uip maestro flow eval evaluator add/list --output json` and pass the generated ID/file ref. Evaluators added later are not auto-attached; rerun `set add` with explicit generated refs or carefully repair `evaluatorRefs` using CLI-created evaluator file refs.

`--entry-point` is stored as `selectedEntrypoint` and accepts `/Main.bpmn#start` or a start node ID such as `start_a1b2c3d4`. `eval run start` uses it unless overridden with `--entry-point`. Pin it when multiple entry points exist; otherwise the first start node found is used.

## Data Point Lifecycle

Data points live inline in the eval set JSON. Run:

```bash
uip maestro flow eval add "<data_point_name>" \
  --set "<set_name>" \
  --inputs '{"...":"..."}' \
  [--expected '{"...":"..."}'] \
  [--criteria '{"<evaluator_id>": {...}}'] \
  [--input-file <key>=<path>] \
  [--search-text "<text>"] \
  --path <flow_project> --output json

uip maestro flow eval list --set "<set_name>" --path <flow_project> --output json

uip maestro flow eval remove "<id_or_name>" --set "<set_name>" --path <flow_project> --output json
```

<a id="--criteria"></a>
<a id="--input-file-keypath"></a>
### Inputs, Expected Values, and Criteria

`--inputs` must contain only keys matching the chosen entry point's declared input variables. If a variable is missing, add it or change the input JSON. To add a string input named `name`, run:

```bash
uip maestro flow variable add ./MySolution/MyFlow/MyFlow.flow name \
  --direction in --type string --output json
```

Evaluator behavior:

- `exact-match`: compares output verbatim, or `expected[targetKey]` when the evaluator has `--target-key`.
- `json-similarity`: tree-compares with tolerance.
- `contains`: does not use `--expected`; use `--search-text`.
- `llm-judge-output`: substitutes `--expected` into `{{ExpectedOutput}}`.
- `llm-judge-strict-json`: substitutes it per key into `{{ExpectedOutput}}`.
- `llm-judge-trajectory`: uses it with `--expected-agent-behavior` set through `--criteria`.
- `llm-judge-trajectory-simulation`: behaves like `trajectory`, with simulation context.

`--criteria` contains per-evaluator overrides keyed by evaluator ID. Use it when evaluators in one set need different criteria:

```json
{
  "<evaluator_ref_for_trajectory>": {
    "expectedAgentBehavior": "Agent calls the weather tool with the user's location, then returns a one-sentence summary."
  },
  "<evaluator_ref_for_output>": {
    "expectedOutput": {"summary": "Sunny in NYC, 72°F"}
  }
}
```

When omitted, output evaluators fall back to `--expected` and trajectory evaluators use defaults. Always provide `expectedAgentBehavior` for trajectory evaluators; scoring against an empty `{{ExpectedAgentBehavior}}` is meaningless.

### File and Contains Inputs

`--input-file <key>=<path>` is repeatable and attaches a staged file under the specified key for runtime use, including PDFs, CSVs, and images. Do not delete the source before the run completes.

`--search-text` is for `contains` evaluators. It attaches the substring to test and is equivalent to writing `criteria` for that evaluator.

## Eval Set JSON Shape

```json
{
  "id": "<uuid>",
  "name": "Smoke Tests",
  "version": "1.0",
  "evaluatorRefs": ["<evaluator-file-ref-1>.json", "<evaluator-file-ref-2>.json"],
  "selectedEntrypoint": "/Main.bpmn#start",
  "evaluations": [
    {
      "id": "<uuid>",
      "name": "hello-test",
      "inputs": {"message": "hello"},
      "expectedOutput": {"reply": "Hello! How can I help you?"},
      "evaluationCriterias": {
        "<evaluator-ref-2>": {
          "expectedAgentBehavior": "Agent responds with a friendly greeting."
        }
      }
    }
  ]
}
```

Keep `version: "1.0"`; it identifies the new eval format. <!-- version-check-skip --> (eval-set file schema version, CLI-emitted by `eval set add` — not a `.flow` version)

- `evaluatorRefs` references CLI-generated evaluator files; prefer CLI commands over hand-editing.
- `selectedEntrypoint` pins the set's entry point; override it per run with `eval run start --entry-point`.
- `evaluations[]` is the inline data-point list; order is informational.
- `evaluationCriterias` (plural) maps per-data-point, per-evaluator overrides.

## Aligning Inputs with the Flow Schema

The data point's `inputs` must match the chosen entry point's input schema. Mismatches produce errors such as `Input "name" is not declared as an input variable in the flow`. Before adding data points, inspect `<flow>.flow` for `variables` entries with `direction: "in"`, or run:

```bash
uip maestro flow variable list <flow_file> --output json
```

## Simulations on Data Points

Simulations replace selected nodes during an eval run with controlled outputs. Target a component by its `.flow` node `id`. Run:

```bash
uip maestro flow eval simulation add <component-id> \
  --set "<set_name>" \
  --data-point "<data_point_name>" \
  --strategy Llm \
  --component-type connector \
  --simulation-instructions "Pretend to send the email and return success." \
  --output-schema '{"type":"object","properties":{"status":{"type":"string"},"messageId":{"type":"string"}}}' \
  --path <flow_project> --output json

uip maestro flow eval simulation add <component-id> \
  --set "<set_name>" \
  --data-point "<data_point_name>" \
  --strategy Static \
  --component-type agent \
  --mock-value '{"status":"ok"}' \
  --path <flow_project> --output json

uip maestro flow eval simulation list \
  --set "<set_name>" \
  --data-point "<data_point_name>" \
  --path <flow_project> --output json

uip maestro flow eval simulation remove <component-id> \
  --set "<set_name>" \
  --data-point "<data_point_name>" \
  --path <flow_project> --output json
```

| Strategy | Use | Required or relevant flags |
|---|---|---|
| `Llm` | Plausible, non-deterministic output | `--simulation-instructions`, `--output-schema` (auto-resolved) |
| `Static` | Identical output every run | `--mock-value <json>` |

For `Llm`, `--output-schema` is auto-resolved from the `.flow` file: connector `outputJsonSchema`, agent `agentOutputVariables`, or `node.outputs`. Pass it explicitly only to override the derived schema or when no outputs are declared.

Simulations are stored inline in the data point's `simulations` array. Adding one for an existing `<component-id>` and data point replaces the existing simulation.

## Anti-patterns

- Do not hand-write data-point `id` UUIDs. Run `uip maestro flow eval add`; the CLI generates fresh UUIDs and maintains `evalSetId`.
- Do not pass `--inputs` keys absent from the flow input schema; the CLI rejects them.
- Do not set `--expected '{}'` while omitting `--criteria` for trajectory evaluators; both placeholders are empty and scoring is meaningless.
- Do not delete attached input files before the run completes; the CLI references them until upload to Studio Web finishes.
- Do not expect `--evaluators` on `set add` to update automatically; later evaluators are not retroactively linked.