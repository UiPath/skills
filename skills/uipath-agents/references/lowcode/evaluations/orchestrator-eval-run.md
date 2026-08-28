# Orchestrator Runtime Eval Commands

Manage runtime evaluations for agents published as Orchestrator packages. Commands call the agents runtime API and are scoped by `--process-key` (process key GUID). Run `uip or processes list` to find process keys.

## Command structure

```text
uip or eval
├── execute-and-evaluate
├── run list / get / results
├── evaluator list / get / create / update / delete
├── eval-set list / get / create / update / delete
├── evaluation list / get / create / update / delete
└── schedule create / list / get / update / pause / resume / delete
```

## execute-and-evaluate

Run an evaluation against a published package. Always pass inline `--items` and `--evaluators`, including when `--eval-set-id` is supplied; inline data is what runs.

```bash
uip or eval execute-and-evaluate \
  --process-key <guid> --workload-id <guid> --items <json> --evaluators <json> \
  [--eval-set-id <guid>] [--batch-size <n>] [--folder-key <folder-guid>] \
  [--tenant <tenant-name>] --output json
```

Required: `--process-key`, `--workload-id` (valid GUID), `--items` (JSON array), and `--evaluators` (JSON array). Optional: `--eval-set-id` (defaults to zero GUID), `--batch-size` (maximum concurrent evaluation pipelines; default `5`), `--folder-key` (folder key GUID; otherwise the personal workspace), and `--tenant`.

Typical item:

```json
{"id":"<id>","name":"<name>","inputs":{},"expectedOutput":{},"expectedBehavior":""}
```

Typical evaluator:

```json
{"id":"<id>","version":"","evaluatorTypeId":"<type-id>","evaluatorConfig":{"name":"<name>","prompt":"<prompt>","model":"<explicit-model-id>","targetOutputKey":"*"}}
```

Output includes `Result`, `Code`, and `Data`. `Code` is `EvalRunSubmitted`; `Data` includes `ProcessKey`, `Folder`, `EvalSetId`, and `EvalSetRunId`.

## Evaluators

Evaluator CRUD is scoped by process key.

```bash
uip or eval evaluator list --process-key <guid> [--limit <n>] [--offset <n>] [--tenant <tenant>] --output json
uip or eval evaluator get <evaluatorId> --process-key <guid> [--tenant <tenant>] --output json
uip or eval evaluator create \
  --process-key <guid> --workload-id <guid> --folder-key <guid> \
  --name <name> --description <text> --evaluator-type-id <id> \
  --evaluator-config <json> [--version <version>] [--tenant <tenant>] --output json
uip or eval evaluator update <evaluatorId> \
  --process-key <guid> [--name <name>] [--description <text>] \
  [--evaluator-type-id <id>] [--evaluator-config <json>] [--version <version>] \
  [--tenant <tenant>] --output json
uip or eval evaluator delete <evaluatorId> --process-key <guid> [--tenant <tenant>] --output json
```

`evaluator list` returns `EvaluatorList` with `EvaluatorId`, `Name`, `Description`, `EvaluatorTypeId`, `Version`, `CreatedAt`, and `Pagination`; `evaluator get` returns `EvaluatorDetails`; create, update, and delete return `EvaluatorCreated`, `EvaluatorUpdated`, and `EvaluatorDeleted`.

Create requires `--process-key`, `--workload-id`, `--folder-key`, `--name`, `--description`, `--evaluator-type-id`, and `--evaluator-config`; `--version` defaults to `1.0`. Evaluator type IDs include `uipath-exact-match`, `uipath-llm-judge-output-semantic-similarity`, and `uipath-llm-judge-trajectory-similarity`. Update requires at least one optional field; fetch current state, merge changes, and PUT the full object because the backend has no PATCH endpoint.

## Eval Sets

Eval sets are dataset containers scoped by process key.

```bash
uip or eval eval-set list --process-key <guid> [--limit <n>] [--offset <n>] [--tenant <tenant>] --output json
uip or eval eval-set get <evalSetId> --process-key <guid> [--tenant <tenant>] --output json
uip or eval eval-set create \
  --process-key <guid> --workload-id <guid> --folder-key <guid> --name <name> \
  [--description <text>] [--batch-size <n>] [--timeout-minutes <n>] \
  [--evaluator-refs <refs...>] [--tenant <tenant>] --output json
uip or eval eval-set update <evalSetId> \
  --process-key <guid> [--name <name>] [--description <text>] \
  [--batch-size <n>] [--timeout-minutes <n>] [--evaluator-refs <refs...>] \
  [--tenant <tenant>] --output json
uip or eval eval-set delete <evalSetId> --process-key <guid> [--tenant <tenant>] --output json
```

`eval-set list` returns `EvalSetList` with `EvalSetId`, `Name`, `Description`, `BatchSize`, `EvaluatorRefs`, `CreatedAt`, and `Pagination`; get returns `EvalSetDetails`; create, update, and delete return `EvalSetCreated`, `EvalSetUpdated`, and `EvalSetDeleted`.

Create requires `--process-key`, `--workload-id`, `--folder-key`, and `--name`. Optional fields are `--description`, `--batch-size`, `--timeout-minutes`, and space-separated evaluator IDs in `--evaluator-refs`. Update requires at least one optional field; fetch, merge, and PUT the full object.

## Evaluation (Data Points)

Evaluations are test cases/data points within eval sets.

```bash
uip or eval evaluation list \
  --process-key <guid> --eval-set-id <guid> [--limit <n>] [--offset <n>] \
  [--tenant <tenant>] --output json
uip or eval evaluation get <evaluationId> \
  --process-key <guid> --eval-set-id <guid> [--tenant <tenant>] --output json
uip or eval evaluation create \
  --process-key <guid> --eval-set-id <guid> --folder-key <guid> --name <name> \
  --inputs <json> [--expected-output <json>] [--expected-behavior <text>] \
  [--evaluation-criterias <json>] [--tenant <tenant>] --output json
uip or eval evaluation update <evaluationId> \
  --process-key <guid> --eval-set-id <guid> [--name <name>] [--inputs <json>] \
  [--expected-output <json>] [--expected-behavior <text>] \
  [--evaluation-criterias <json>] [--tenant <tenant>] --output json
uip or eval evaluation delete <evaluationId> \
  --process-key <guid> --eval-set-id <guid> [--tenant <tenant>] --output json
```

`evaluation list` returns `EvaluationList` with `EvaluationId`, `EvalSetId`, `Name`, `Inputs`, `ExpectedOutput`, `ExpectedBehavior`, `CreatedAt`, and `Pagination`; get returns `EvaluationDetails`; create, update, and delete return `EvaluationCreated`, `EvaluationUpdated`, and `EvaluationDeleted`.

Create requires `--process-key`, `--eval-set-id`, `--folder-key`, `--name`, and `--inputs`. Optional fields are `--expected-output`, `--expected-behavior`, and `--evaluation-criterias`, the backend spelling for per-evaluator criteria overrides. Update requires at least one optional field; fetch, merge, and PUT the full object.

## Run Results

Query runs by process key.

```bash
uip or eval run list --process-key <guid> [--limit <n>] [--offset <n>] [--tenant <tenant>] --output json
uip or eval run get <evalSetRunId> --process-key <guid> [--tenant <tenant>] --output json
uip or eval run results <evalSetRunId> --process-key <guid> [--tenant <tenant>] --output json
```

`run list` returns `EvalSetRunList` with `EvalSetRunId`, `EvalSetId`, `Status`, `Score`, `EvalsExecuted`, `Duration`, `CreatedAt`, and `Pagination`; `run get` returns `EvalSetRunDetails`; `run results` returns `EvalRunResults` with `EvalRunId`, `DataPoint`, `Status`, `Result`, and `CreatedAt`.

## Schedules

Manage recurring evaluation runs.

```bash
uip or eval schedule create \
  --process-key <guid> --eval-set-id <guid> --cron <expression> \
  [--workload-id <guid>] [--folder-key <guid>] [--tenant <tenant>] --output json
uip or eval schedule list --process-key <guid> --output json
uip or eval schedule get <scheduleId> --process-key <guid> --output json
uip or eval schedule update <scheduleId> --process-key <guid> [--eval-set-id <guid>] [--cron <expr>] --output json
uip or eval schedule pause <scheduleId> --process-key <guid> --output json
uip or eval schedule resume <scheduleId> --process-key <guid> --output json
uip or eval schedule delete <scheduleId> --process-key <guid> --output json
```

Create requires `--process-key`, `--eval-set-id`, and `--cron`. `--workload-id` and `--folder-key` resolve from the eval set when omitted and override it when supplied. It returns `EvalScheduleCreated` with `ScheduleId`, `WorkloadId`, `ProcessKey`, `FolderKey`, `EvalSetId`, `CronExpression`, `Status`, and `CreatedAt`. Other output codes are `EvalScheduleList`, `EvalScheduleDetails`, `EvalScheduleUpdated`, `EvalSchedulePaused`, `EvalScheduleResumed`, and `EvalScheduleDeleted`. Update requires at least one of `--eval-set-id` or `--cron`; folder key is immutable after creation.

## Typical workflow — CRUD-first

1. Run `uip or eval evaluator create` with `--process-key`, `--workload-id`, `--folder-key`, `--name`, `--description`, `--evaluator-type-id`, and valid `--evaluator-config` JSON; capture the evaluator ID.
2. Run `uip or eval eval-set create` with `--process-key`, `--workload-id`, `--folder-key`, `--name`, and `--evaluator-refs`; capture the eval set ID.
3. Run `uip or eval evaluation create` with `--process-key`, `--eval-set-id`, `--folder-key`, `--name`, `--inputs`, and applicable expected values.
4. Run `uip or eval eval-set update` with `--evaluator-refs` to add or replace linked evaluator IDs when needed.
5. Run `uip or eval execute-and-evaluate` with `--process-key`, `--workload-id`, `--eval-set-id`, inline `--items`, and inline `--evaluators`; copy canonical CRUD data into the inline arguments.
6. Run `uip or eval run list` and `uip or eval run results <evalSetRunId>` with `--process-key` to inspect results.
7. Run `uip or eval schedule create` with `--process-key`, `--eval-set-id`, and `--cron`; `--workload-id` and `--folder-key` resolve from the eval set when omitted.

Keep CRUD data and inline execution data synchronized. `--eval-set-id` does not automatically use CRUD items or evaluators.

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `401 Unauthorized` | Auth expired | Run `uip login`. |
| `Authentication failed` | No active session | Run `uip login` first. |
| `Process not found` | Invalid process key | Verify with `uip or processes list`. |
| `personal workspace not found` | No personal workspace | Pass `--folder-key` explicitly. |
| `WorkloadId must not be equal to zero GUID` | Missing or zero `--workload-id` | Pass a valid workload ID GUID. |
| `--items is not a valid JSON array` | Malformed JSON | Check JSON syntax; it must be an array of objects. |
| `--evaluator-config is not valid JSON` | Malformed JSON | Pass a valid JSON object. |

## Anti-patterns

- **Do not pass `evaluatorConfig: {}` in `--evaluators`.** LLM-based evaluators (types 5, 7) require `prompt`, `model`, and `targetOutputKey`; an empty config fails at runtime.
- **Do not pass `"model": "same-as-agent"` in inline evaluator configs.** Runtime evals cannot read `agent.json` to resolve it; pass an explicit model ID.
- **Do not omit `--folder-key` on create commands when targeting a non-personal workspace.** The personal-workspace fallback works only for `execute-and-evaluate`; `evaluator create`, `eval-set create`, and `evaluation create` require `--folder-key` explicitly.
- **Keep CRUD data and inline `execute-and-evaluate` items synchronized.** `execute-and-evaluate` requires inline `--items` and `--evaluators` even with `--eval-set-id`; divergence produces confusing results.
- **Do not reuse evaluator IDs across processes.** Evaluators are scoped to a process key; IDs from another process fail.