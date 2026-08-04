# Orchestrator Runtime Eval Commands

Manage and run runtime evaluations for agents published as Orchestrator packages. All commands are scoped by `--process-key` (deployment GUID) and hit the agents runtime API.

## Command Structure

```
uip or eval
├── execute-and-evaluate             Submit a runtime eval run
├── run list                         List eval set runs for a process
├── run get <evalSetRunId>           Get details of a specific run
├── run results <evalSetRunId>       View per-item results
├── evaluator list/get/create/delete Manage evaluators
├── eval-set list/get/create/delete  Manage eval sets (dataset containers)
├── evaluation list/get/create/delete Manage data points within eval sets
└── schedule create/list/get/update/pause/resume/delete
                                     Manage scheduled recurring eval runs
```

---

## execute-and-evaluate

Submit a runtime eval run for a published Orchestrator package.

```bash
uip or eval execute-and-evaluate \
  --process-key <guid> \
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
| `--process-key` | Yes | Process key (GUID). Use `uip or processes list` to find keys. |
| `--items` | Yes | JSON array of eval items. See [Evaluations](#evaluation-data-points). |
| `--evaluators` | Yes | JSON array of evaluator configs. See [Evaluators](#evaluators). |
| `--eval-set-id` | No | Eval set ID; defaults to zero GUID |
| `--batch-size` | No | Max concurrent evaluation pipelines (default: `5`) |
| `--folder-key` | No | Folder key GUID; defaults to personal workspace |
| `--tenant` | No | UiPath tenant name |

The folder resolves from your personal workspace automatically. Pass `--folder-key` to target a specific folder.

### Example

```bash
uip or eval execute-and-evaluate \
  --process-key "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09" \
  --items '[{"id":"i1","name":"Test","inputs":{"input":"hello"},"expectedOutput":{},"expectedBehavior":""}]' \
  --evaluators '[{"id":"ev-1","version":"","evaluatorTypeId":"5","evaluatorConfig":{"name":"Semantic","category":1,"type":5,"prompt":"Score 0-100...","model":"gpt-4.1-2025-04-14","targetOutputKey":"*"}}]' \
  --output json
```

### Output

```json
{
  "Result": "Success",
  "Code": "EvalRunSubmitted",
  "Data": {
    "ProcessKey": "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09",
    "Folder": "user@uipath.com's workspace",
    "EvalSetId": "00000000-0000-0000-0000-000000000000",
    "EvalSetRunId": "f3a7d219-8b4c-4e62-a951-7d3f6e2c8b04"
  }
}
```

---

## Evaluators

CRUD for evaluators scoped by process key.

### evaluator list

```bash
uip or eval evaluator list --process-key <guid> [--tenant <tenant>] --output json
```

Output code: `EvaluatorList`. Fields: EvaluatorId, Name, Description, EvaluatorTypeId, Version, CreatedAt.

### evaluator get

```bash
uip or eval evaluator get <evaluatorId> --process-key <guid> [--tenant <tenant>] --output json
```

Output code: `EvaluatorDetails`.

### evaluator create

```bash
uip or eval evaluator create \
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
| `--workload-id` | Yes | Workload ID (GUID) |
| `--folder-key` | Yes | Folder key (GUID) |
| `--name` | Yes | Evaluator name |
| `--description` | Yes | Evaluator description |
| `--evaluator-type-id` | Yes | Type ID (e.g. `1`=exact-match, `5`=semantic-similarity, `6`=json-similarity, `7`=trajectory) |
| `--evaluator-config` | Yes | Evaluator config as JSON object |
| `--version` | No | Version string (default: `1.0`) |

Output code: `EvaluatorCreated`.

### evaluator delete

```bash
uip or eval evaluator delete <evaluatorId> --process-key <guid> [--tenant <tenant>] --output json
```

Output code: `EvaluatorDeleted`.

---

## Eval Sets

CRUD for eval sets (dataset containers) scoped by process key.

### eval-set list

```bash
uip or eval eval-set list --process-key <guid> [--tenant <tenant>] --output json
```

Output code: `EvalSetList`. Fields: EvalSetId, Name, Version, Description, BatchSize, EvaluatorRefs, CreatedAt.

### eval-set get

```bash
uip or eval eval-set get <evalSetId> --process-key <guid> [--tenant <tenant>] --output json
```

Output code: `EvalSetDetails`.

### eval-set create

```bash
uip or eval eval-set create \
  --process-key <guid> \
  --workload-id <guid> \
  --folder-key <guid> \
  --name <name> \
  [--version <version>] \
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
| `--workload-id` | Yes | Workload ID (GUID) |
| `--folder-key` | Yes | Folder key (GUID) |
| `--name` | Yes | Eval set name |
| `--version` | No | Version (default: `1.0`) |
| `--description` | No | Description |
| `--batch-size` | No | Max concurrent evaluations |
| `--timeout-minutes` | No | Timeout per evaluation |
| `--evaluator-refs` | No | Evaluator IDs to link (space-separated) |

Output code: `EvalSetCreated`.

### eval-set delete

```bash
uip or eval eval-set delete <evalSetId> --process-key <guid> [--tenant <tenant>] --output json
```

Output code: `EvalSetDeleted`.

---

## Evaluation (Data Points)

CRUD for evaluations (test cases / data points) within eval sets.

### evaluation list

```bash
uip or eval evaluation list \
  --process-key <guid> \
  --eval-set-id <guid> \
  [--tenant <tenant>] \
  --output json
```

Output code: `EvaluationList`. Fields: EvaluationId, EvalSetId, Name, Inputs, ExpectedOutput, ExpectedBehavior, CreatedAt.

### evaluation get

```bash
uip or eval evaluation get <evaluationId> \
  --process-key <guid> \
  --eval-set-id <guid> \
  [--tenant <tenant>] \
  --output json
```

Output code: `EvaluationDetails`.

### evaluation create

```bash
uip or eval evaluation create \
  --process-key <guid> \
  --eval-set-id <guid> \
  --folder-key <guid> \
  --name <name> \
  --inputs <json> \
  [--expected-output <json>] \
  [--expected-behavior <text>] \
  [--evaluation-criterias <json>] \
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

Output code: `EvaluationCreated`.

### evaluation delete

```bash
uip or eval evaluation delete <evaluationId> \
  --process-key <guid> \
  --eval-set-id <guid> \
  [--tenant <tenant>] \
  --output json
```

Output code: `EvaluationDeleted`.

---

## Run Results

Query eval run results by process key.

### run list

```bash
uip or eval run list --process-key <guid> [--limit <n>] [--tenant <tenant>] --output json
```

Output code: `EvalSetRunList`. Fields: EvalSetRunId, EvalSetId, Status, Score, EvalsExecuted, Duration, CreatedAt.

### run get

```bash
uip or eval run get <evalSetRunId> --process-key <guid> [--tenant <tenant>] --output json
```

Output code: `EvalSetRunDetails`.

### run results

```bash
uip or eval run results <evalSetRunId> --process-key <guid> [--tenant <tenant>] --output json
```

Output code: `EvalRunResults`. Fields: EvalRunId, DataPoint, Status, Result, CreatedAt.

---

## Schedules

CRUD for scheduled recurring eval runs.

### schedule create

```bash
uip or eval schedule create \
  --process-key <guid> \
  --workload-id <guid> \
  --eval-set-id <guid> \
  --cron <expression> \
  --folder-key <guid> \
  [--tenant <tenant>] \
  --output json
```

All flags are required except `--tenant`. Cron is a five-field UTC expression (e.g. `"0 9 * * *"`).

Output code: `EvalScheduleCreated`. Fields: ScheduleId, WorkloadId, ProcessKey, FolderKey, EvalSetId, CronExpression, Status, CreatedAt.

### schedule list / get / update / pause / resume / delete

```bash
uip or eval schedule list --process-key <guid> --output json
uip or eval schedule get <scheduleId> --process-key <guid> --output json
uip or eval schedule update <scheduleId> --process-key <guid> [--eval-set-id <guid>] [--cron <expr>] --output json
uip or eval schedule pause <scheduleId> --process-key <guid> --output json
uip or eval schedule resume <scheduleId> --process-key <guid> --output json
uip or eval schedule delete <scheduleId> --process-key <guid> --output json
```

Output codes: `EvalScheduleList`, `EvalScheduleDetails`, `EvalScheduleUpdated`, `EvalSchedulePaused`, `EvalScheduleResumed`, `EvalScheduleDeleted`.

Update requires at least one of `--eval-set-id` or `--cron`. Folder key is immutable after creation.

---

## Typical Workflow

```bash
# 1. Create evaluators
uip or eval evaluator create \
  --process-key "$PROCESS_KEY" --workload-id "$WORKLOAD_ID" --folder-key "$FOLDER_KEY" \
  --name "Semantic Similarity" --description "LLM output comparison" \
  --evaluator-type-id 5 \
  --evaluator-config '{"name":"Semantic","type":5,"category":1,"prompt":"Score 0-100...","model":"gpt-4.1-2025-04-14","targetOutputKey":"*"}' \
  --output json

# 2. Create an eval set linking the evaluator
uip or eval eval-set create \
  --process-key "$PROCESS_KEY" --workload-id "$WORKLOAD_ID" --folder-key "$FOLDER_KEY" \
  --name "Smoke Tests" --evaluator-refs "$EVALUATOR_ID" \
  --output json

# 3. Add data points
uip or eval evaluation create \
  --process-key "$PROCESS_KEY" --eval-set-id "$EVAL_SET_ID" --folder-key "$FOLDER_KEY" \
  --name "Greeting test" --inputs '{"input":"hello"}' \
  --expected-output '{"content":"Hi there!"}' \
  --output json

# 4. Run the eval
uip or eval execute-and-evaluate \
  --process-key "$PROCESS_KEY" \
  --items '[{"id":"i1","name":"Greeting test","inputs":{"input":"hello"},"expectedOutput":{"content":"Hi there!"},"expectedBehavior":""}]' \
  --evaluators '[{"id":"ev-1","evaluatorTypeId":"5","evaluatorConfig":{}}]' \
  --output json

# 5. Check results
uip or eval run list --process-key "$PROCESS_KEY" --output json
uip or eval run results "$EVAL_SET_RUN_ID" --process-key "$PROCESS_KEY" --output json

# 6. Schedule recurring runs
uip or eval schedule create \
  --process-key "$PROCESS_KEY" --workload-id "$WORKLOAD_ID" \
  --eval-set-id "$EVAL_SET_ID" --folder-key "$FOLDER_KEY" \
  --cron "0 9 * * *" --output json
```

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Auth expired | Run `uip login` |
| `Authentication failed` | No active session | Run `uip login` first |
| `Process not found` | Invalid process key | Verify with `uip or processes list` |
| `personal workspace not found` | No personal workspace | Pass `--folder-key` explicitly |
| `--items is not a valid JSON array` | Malformed JSON | Check JSON syntax; must be array of objects |
| `--evaluator-config is not valid JSON` | Malformed JSON | Pass a valid JSON object |
