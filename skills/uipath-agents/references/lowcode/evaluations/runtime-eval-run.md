# Runtime Eval Commands

Manage and run runtime evaluations for agents published as Orchestrator packages. All commands are scoped by `--process-key` (process key GUID) and hit the agents runtime API.

## Command Structure

```
uip eval
├── execute-and-evaluate             Submit a runtime eval run (eval-set or inline mode)
├── run list                         List eval set runs for a process
├── run get <evalSetRunId>           Get details of a specific run
├── run results <evalSetRunId>       View per-item results
├── evaluator list/get/create/update/delete Manage evaluators
├── eval-set list/get/create/update/delete  Manage eval sets (dataset containers)
├── evaluation list/get/create/update/delete Manage data points within eval sets
├── simulatable-components list      List tools/components available for simulation
└── schedule create/list/get/update/pause/resume/delete
                                     Manage scheduled recurring eval runs
```

---

## execute-and-evaluate

Submit a runtime eval run for a published Orchestrator package. Two modes:

### Eval-set mode (recommended)

Pass `--eval-set-id` alone — the CLI fetches evaluations (including simulations) and evaluators from the eval set automatically.

```bash
uip eval execute-and-evaluate \
  --process-key <guid> \
  --eval-set-id <guid> \
  [--batch-size <n>] \
  [--folder-key <folder-guid>] \
  [--tenant <tenant-name>] \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--process-key` | Yes | Process key (GUID). Use `uip or processes list` to find keys. |
| `--eval-set-id` | Yes | Eval set ID. Fetches evaluations and evaluators automatically. |
| `--batch-size` | No | Override eval set's batch size (default: eval set's value, or `5`) |
| `--folder-key` | No | Override eval set's folder key |
| `--tenant` | No | UiPath tenant name |

### Inline mode

Pass `--items` and `--evaluators` directly for full control. Requires `--workload-id`.

```bash
uip eval execute-and-evaluate \
  --process-key <guid> \
  --workload-id <guid> \
  --items <json> \
  --evaluators <json> \
  [--eval-set-id <guid>] \
  [--batch-size <n>] \
  [--folder-key <folder-guid>] \
  [--tenant <tenant-name>] \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--process-key` | Yes | Process key (GUID). |
| `--workload-id` | Yes (inline) | Workload ID (GUID). Use your Studio Web project ID or agent ID. |
| `--items` | Yes (inline) | JSON array of eval items. See [Evaluations](#evaluation-data-points). |
| `--evaluators` | Yes (inline) | JSON array of evaluator configs. See [Evaluators](#evaluators). |
| `--eval-set-id` | No | Eval set ID; defaults to zero GUID in inline mode |
| `--batch-size` | No | Max concurrent evaluation pipelines (default: `5`) |
| `--folder-key` | No | Folder key GUID; defaults to personal workspace |
| `--tenant` | No | UiPath tenant name |

### Example (eval-set mode)

```bash
uip eval execute-and-evaluate \
  --process-key "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09" \
  --eval-set-id "f3a7d219-8b4c-4e62-a951-7d3f6e2c8b04" \
  --output json
```

### Example (inline mode)

```bash
uip eval execute-and-evaluate \
  --process-key "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09" \
  --workload-id "a1b2c3d4-0000-0000-0000-000000000001" \
  --items '[{"id":"i1","name":"Test","inputs":{"input":"hello"},"expectedOutput":{},"expectedBehavior":""}]' \
  --evaluators '[{"id":"ev-1","version":"1.0","evaluatorTypeId":"uipath-llm-judge-output-semantic-similarity","evaluatorConfig":{"name":"Semantic","prompt":"Score 0-100...","model":"anthropic.claude-sonnet-4-6","targetOutputKey":"*"}}]' \
  --output json
```

### Output

```json
{
  "Result": "Success",
  "Code": "EvalRunSubmitted",
  "Data": {
    "ProcessKey": "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09",
    "Folder": "a1b2c3d4-folder-key",
    "EvalSetId": "f3a7d219-8b4c-4e62-a951-7d3f6e2c8b04",
    "EvalSetRunId": "a1b2c3d4-0000-0000-0000-000000000101"
  }
}
```

---

## Simulatable Components

List tools, escalations, and MCP tools available for simulation on a deployed process.

### simulatable-components list

```bash
uip eval simulatable-components list \
  --process-key <guid> \
  [--process-version <version>] \
  [--tenant <tenant>] \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--process-key` | Yes | Process key (GUID) |
| `--process-version` | No | Semantic version; defaults to latest deployed version |
| `--tenant` | No | UiPath tenant name |

Output code: `SimulatableComponentList`. Each component has: Id, Name, Description, ComponentType (`tool`, `escalation`, `mcpTool`), SubType, IsEnabled, OutputSchema (when available).

Use component IDs from this command when configuring `--simulations` on evaluations.

---

## Evaluators

CRUD for evaluators scoped by process key.

### evaluator list

```bash
uip eval evaluator list --process-key <guid> [--limit <n>] [--offset <n>] [--tenant <tenant>] --output json
```

Output code: `EvaluatorList`. Fields: EvaluatorId, ExternalId, Name, Description, EvaluatorTypeId, Version, CreatedAt. Includes `Pagination` field.

> **Important**: Use the `ExternalId` (not `EvaluatorId`) when linking evaluators to eval sets via `--evaluator-refs`.

### evaluator get

```bash
uip eval evaluator get <evaluatorId> --process-key <guid> [--tenant <tenant>] --output json
```

Output code: `EvaluatorDetails`.

### evaluator create

```bash
uip eval evaluator create \
  --process-key <guid> \
  --workload-id <guid> \
  --folder-key <guid> \
  --name <name> \
  --description <text> \
  --evaluator-type-id <id> \
  --evaluator-config <json> \
  [--version <version>] \
  [--tenant <tenant>] \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--process-key` | Yes | Process key (GUID) |
| `--workload-id` | Yes | Workload ID (GUID) — use Studio Web project ID or agent ID |
| `--folder-key` | Yes | Folder key (GUID) |
| `--name` | Yes | Evaluator name |
| `--description` | Yes | Evaluator description |
| `--evaluator-type-id` | Yes | Type ID (e.g. `uipath-exact-match`, `uipath-llm-judge-output-semantic-similarity`, `uipath-llm-judge-trajectory-similarity`) |
| `--evaluator-config` | Yes | Evaluator config as JSON object. **Must include `name` field inside the JSON.** |
| `--version` | No | Version string (default: `1.0`) |

Output code: `EvaluatorCreated`.

> **Important**: The `--evaluator-config` JSON must include a `name` field. Without it, the Python eval worker fails with `typing.Any must be a subclass of BaseEvaluatorConfig`.

### evaluator update

```bash
uip eval evaluator update <evaluatorId> \
  --process-key <guid> \
  [--name <name>] \
  [--description <text>] \
  [--evaluator-type-id <id>] \
  [--evaluator-config <json>] \
  [--version <version>] \
  [--tenant <tenant>] \
  --output json
```

At least one optional field must be provided. The command fetches the current state, merges your changes, and PUTs the full object back (the backend has no PATCH endpoint).

Output code: `EvaluatorUpdated`.

### evaluator delete

```bash
uip eval evaluator delete <evaluatorId> --process-key <guid> [--tenant <tenant>] --output json
```

Output code: `EvaluatorDeleted`.

---

## Eval Sets

CRUD for eval sets (dataset containers) scoped by process key.

### eval-set list

```bash
uip eval eval-set list --process-key <guid> [--limit <n>] [--offset <n>] [--tenant <tenant>] --output json
```

Output code: `EvalSetList`. Fields: EvalSetId, Name, Description, Version, BatchSize, EvaluatorRefs, CreatedAt. Includes `Pagination` field.

### eval-set get

```bash
uip eval eval-set get <evalSetId> --process-key <guid> [--tenant <tenant>] --output json
```

Output code: `EvalSetDetails`.

### eval-set create

```bash
uip eval eval-set create \
  --process-key <guid> \
  --workload-id <guid> \
  --folder-key <guid> \
  --name <name> \
  [--description <text>] \
  [--batch-size <n>] \
  [--timeout-minutes <n>] \
  [--evaluator-refs <refs...>] \
  [--tenant <tenant>] \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--process-key` | Yes | Process key (GUID) |
| `--workload-id` | Yes | Workload ID (GUID) — use Studio Web project ID or agent ID |
| `--folder-key` | Yes | Folder key (GUID) |
| `--name` | Yes | Eval set name |
| `--description` | No | Description |
| `--batch-size` | No | Max concurrent evaluations |
| `--timeout-minutes` | No | Timeout per evaluation |
| `--evaluator-refs` | No | Evaluator ExternalIds to link (space-separated) |

Output code: `EvalSetCreated`.

### eval-set update

```bash
uip eval eval-set update <evalSetId> \
  --process-key <guid> \
  [--name <name>] \
  [--description <text>] \
  [--batch-size <n>] \
  [--timeout-minutes <n>] \
  [--evaluator-refs <refs...>] \
  [--tenant <tenant>] \
  --output json
```

At least one optional field must be provided. Fetches current state, merges changes, PUTs the full object.

Output code: `EvalSetUpdated`.

### eval-set delete

```bash
uip eval eval-set delete <evalSetId> --process-key <guid> [--tenant <tenant>] --output json
```

Output code: `EvalSetDeleted`.

---

## Evaluation (Data Points)

CRUD for evaluations (test cases / data points) within eval sets.

### evaluation list

```bash
uip eval evaluation list \
  --process-key <guid> \
  --eval-set-id <guid> \
  [--limit <n>] \
  [--offset <n>] \
  [--tenant <tenant>] \
  --output json
```

Output code: `EvaluationList`. Fields: EvaluationId, EvalSetId, Name, Inputs, ExpectedOutput, ExpectedBehavior, Simulations (when present), CreatedAt. Includes `Pagination` field.

### evaluation get

```bash
uip eval evaluation get <evaluationId> \
  --process-key <guid> \
  --eval-set-id <guid> \
  [--tenant <tenant>] \
  --output json
```

Output code: `EvaluationDetails`.

### evaluation create

```bash
uip eval evaluation create \
  --process-key <guid> \
  --eval-set-id <guid> \
  --folder-key <guid> \
  --name <name> \
  --inputs <json> \
  [--expected-output <json>] \
  [--expected-behavior <text>] \
  [--evaluation-criterias <json>] \
  [--simulations <json>] \
  [--tenant <tenant>] \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--process-key` | Yes | Process key (GUID) |
| `--eval-set-id` | Yes | Eval set ID (GUID) |
| `--folder-key` | Yes | Folder key (GUID) |
| `--name` | Yes | Data point name |
| `--inputs` | Yes | Input values as JSON |
| `--expected-output` | No | Expected output as JSON (for output evaluators) |
| `--expected-behavior` | No | Expected agent behavior (for trajectory evaluators) |
| `--evaluation-criterias` | No | Per-evaluator criteria overrides as JSON |
| `--simulations` | No | JSON array of tool simulations. See [Simulations](#simulations). |

Output code: `EvaluationCreated`.

### evaluation update

```bash
uip eval evaluation update <evaluationId> \
  --process-key <guid> \
  --eval-set-id <guid> \
  [--name <name>] \
  [--inputs <json>] \
  [--expected-output <json>] \
  [--expected-behavior <text>] \
  [--evaluation-criterias <json>] \
  [--simulations <json>] \
  [--tenant <tenant>] \
  --output json
```

At least one optional field must be provided. Fetches current state, merges changes, PUTs the full object.

Output code: `EvaluationUpdated`.

### evaluation delete

```bash
uip eval evaluation delete <evaluationId> \
  --process-key <guid> \
  --eval-set-id <guid> \
  [--tenant <tenant>] \
  --output json
```

Output code: `EvaluationDeleted`.

---

## Simulations

Simulations control how the agent's tools behave during evaluation. Instead of calling real external services, the tool's response is simulated.

### Simulation strategies

| Strategy | Value | What it does |
|----------|-------|--------------|
| **Llm** | `0` (default) | LLM generates tool response based on instruction and output schema |
| **Mockito** | `1` | Rule-based behavior matching (uses `behaviors` field) |
| **Static** | `2` | Returns a fixed value (uses `mockValue` field) |

### Adding simulations to evaluations

Pass `--simulations` on `evaluation create` or `evaluation update`. Each simulation needs `componentId` and `componentType` (from `simulatable-components list`):

```bash
# LLM simulation — outputSchema auto-resolved
uip eval evaluation create \
  --process-key "$PROCESS_KEY" --eval-set-id "$EVAL_SET_ID" --folder-key "$FOLDER_KEY" \
  --name "Sim test" --inputs '{"input":"hello"}' \
  --simulations '[{"componentId":"web-search","componentType":"tool","simulationInstruction":"Return search results"}]' \
  --output json

# Static simulation — fixed mock value
uip eval evaluation update <id> \
  --process-key "$PROCESS_KEY" --eval-set-id "$EVAL_SET_ID" \
  --simulations '[{"componentId":"order-lookup","componentType":"tool","simulationStrategy":2,"mockValue":{"status":"shipped"}}]' \
  --output json
```

For LLM strategy (default), `outputSchema` is auto-resolved from the simulatable components API at save time.

### Simulation fields

| Field | Required | Description |
|-------|----------|-------------|
| `componentId` | Yes | Component ID from `simulatable-components list` |
| `componentType` | Yes | `"tool"`, `"escalation"`, or `"mcpTool"` |
| `simulationStrategy` | No | `0` (Llm), `1` (Mockito), `2` (Static) |
| `simulationInstruction` | No | LLM instructions for generating response |
| `mockValue` | No | Fixed return value for Static strategy |
| `outputSchema` | No | Auto-resolved for LLM; pass manually to override |
| `behaviors` | No | Rule-based behaviors for Mockito strategy |
| `childSimulations` | No | Nested simulations for child components |

Simulations stored on evaluations are passed through automatically in eval-set mode `execute-and-evaluate`.

---

## Run Results

Query eval run results by process key.

### run list

```bash
uip eval run list --process-key <guid> [--limit <n>] [--offset <n>] [--tenant <tenant>] --output json
```

Output code: `EvalSetRunList`. Fields: EvalSetRunId, EvalSetId, Status, Score, EvalsExecuted, Duration, CreatedAt. Includes `Pagination` field.

### run get

```bash
uip eval run get <evalSetRunId> --process-key <guid> [--tenant <tenant>] --output json
```

Output code: `EvalSetRunDetails`.

### run results

```bash
uip eval run results <evalSetRunId> --process-key <guid> [--tenant <tenant>] --output json
```

Output code: `EvalRunResults`. Fields: EvalRunId, DataPoint, Status, Result, CreatedAt.

---

## Schedules

CRUD for scheduled recurring eval runs.

### schedule create

```bash
uip eval schedule create \
  --process-key <guid> \
  --eval-set-id <guid> \
  --cron <expression> \
  [--workload-id <guid>] \
  [--folder-key <guid>] \
  [--tenant <tenant>] \
  --output json
```

`--process-key`, `--eval-set-id`, and `--cron` are required. `--workload-id` and `--folder-key` are auto-resolved from the eval set when omitted. Pass them explicitly to override.

Output code: `EvalScheduleCreated`. Fields: ScheduleId, WorkloadId, ProcessKey, FolderKey, EvalSetId, CronExpression, Status, CreatedAt.

### schedule list / get / update / pause / resume / delete

```bash
uip eval schedule list --process-key <guid> --output json
uip eval schedule get <scheduleId> --process-key <guid> --output json
uip eval schedule update <scheduleId> --process-key <guid> [--eval-set-id <guid>] [--cron <expr>] --output json
uip eval schedule pause <scheduleId> --process-key <guid> --output json
uip eval schedule resume <scheduleId> --process-key <guid> --output json
uip eval schedule delete <scheduleId> --process-key <guid> --output json
```

Output codes: `EvalScheduleList`, `EvalScheduleDetails`, `EvalScheduleUpdated`, `EvalSchedulePaused`, `EvalScheduleResumed`, `EvalScheduleDeleted`.

Update requires at least one of `--eval-set-id` or `--cron`. Folder key is immutable after creation.

---

## Typical Workflow — eval-set mode (recommended)

Create evaluators, eval sets, and data points via CRUD, then run from the eval set.

```bash
# 1. Check agent's tools (for simulations)
uip eval simulatable-components list --process-key "$PROCESS_KEY" --output json

# 2. Create an evaluator (name inside evaluatorConfig is required)
uip eval evaluator create \
  --process-key "$PROCESS_KEY" --workload-id "$WORKLOAD_ID" --folder-key "$FOLDER_KEY" \
  --name "LLM Judge Evaluator" --description "Semantic similarity scorer" \
  --evaluator-type-id uipath-llm-judge-output-semantic-similarity \
  --evaluator-config '{"name":"LLM Judge Evaluator","targetOutputKey":"*","prompt":"As an expert evaluator, analyze the semantic similarity of these JSON contents to determine a score from 0-100.\n----\nExpectedOutput:\n{{ExpectedOutput}}\n----\nActualOutput:\n{{ActualOutput}}\n","temperature":0,"maxTokens":8192,"model":"anthropic.claude-sonnet-4-6","defaultEvaluationCriteria":{"expectedOutput":{}}}' \
  --output json

# 3. Create an eval set linking the evaluator (use ExternalId from step 2)
uip eval eval-set create \
  --process-key "$PROCESS_KEY" --workload-id "$WORKLOAD_ID" --folder-key "$FOLDER_KEY" \
  --name "Smoke Tests" --evaluator-refs "$EVALUATOR_EXTERNAL_ID" \
  --output json

# 4. Add data points (with optional simulations)
uip eval evaluation create \
  --process-key "$PROCESS_KEY" --eval-set-id "$EVAL_SET_ID" --folder-key "$FOLDER_KEY" \
  --name "Greeting test" --inputs '{"input":"hello"}' \
  --expected-output '{"content":"Hi there!"}' \
  --simulations '[{"componentId":"escalate_escalation_1","componentType":"escalation","simulationInstruction":"Approve with a positive comment"}]' \
  --output json

# 5. Run — CLI fetches evaluations + evaluators from the eval set automatically
uip eval execute-and-evaluate \
  --process-key "$PROCESS_KEY" --eval-set-id "$EVAL_SET_ID" --output json

# 6. Check results
uip eval run list --process-key "$PROCESS_KEY" --output json
uip eval run results "$EVAL_SET_RUN_ID" --process-key "$PROCESS_KEY" --output json

# 7. Schedule recurring runs
uip eval schedule create \
  --process-key "$PROCESS_KEY" --eval-set-id "$EVAL_SET_ID" \
  --cron "0 9 * * *" --output json
```

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Auth expired | Run `uip login` |
| `424 Failed to check folder permission in AuthZ` | Session expired or wrong folder | Re-login with `uip login --authority <url>` |
| `Authentication failed` | No active session | Run `uip login` first |
| `Process not found` | Invalid process key | Verify with `uip or processes list` |
| `personal workspace not found` | No personal workspace | Pass `--folder-key` explicitly |
| `typing.Any must be a subclass of BaseEvaluatorConfig` | Evaluator config missing `name` | Update evaluator: add `"name"` inside `--evaluator-config` JSON |
| `WorkloadId must not be equal to zero GUID` | Missing or zero `--workload-id` | Pass your Studio Web project ID or agent ID |
| `The eval set has no evaluations (data points)` | Empty eval set | Add evaluations with `uip eval evaluation create` |
| `--items is not a valid JSON array` | Malformed JSON | Check JSON syntax; must be array of objects |
| `--simulations is not a valid JSON array` | Malformed simulations JSON | Each object needs `componentId` and `componentType` |
| `--evaluator-config is not valid JSON` | Malformed JSON | Pass a valid JSON object |
| `Evaluator ... not found` | Wrong ID in `--evaluator-refs` | Use the evaluator's `ExternalId`, not `EvaluatorId` |

## Anti-patterns

- **Don't pass `evaluatorConfig: {}` (empty) in `--evaluators`.** LLM-based evaluators need `name`, `prompt`, `model`, and `targetOutputKey` in the config. An empty config will fail at runtime.
- **Don't forget `name` inside `--evaluator-config`.** The Python eval worker requires it. Without it you get `typing.Any must be a subclass of BaseEvaluatorConfig`.
- **Don't pass `"model": "same-as-agent"` in inline evaluator configs.** Runtime evals have no access to `agent.json` to resolve this. Use an explicit model ID like `anthropic.claude-sonnet-4-6`.
- **Don't forget `--folder-key` on create commands when not using the personal workspace.** The default personal workspace fallback only works for `execute-and-evaluate` inline mode. CRUD commands require `--folder-key` explicitly.
- **Don't reuse evaluator IDs across different processes.** Evaluators are scoped to a process key. Using IDs from one process in another will fail.
- **Use `--evaluator-refs` with ExternalId, not EvaluatorId.** The eval set links evaluators by their `ExternalId` field.
