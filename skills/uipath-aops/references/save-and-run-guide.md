# Save-and-Run Guide

`uip aops pipeline save-and-run --file` persists a new pipeline AND immediately queues its first execution. One round-trip; returns the persisted pipeline plus the first execution's id.

## When to use which verb

| Goal | Verb |
|---|---|
| Author the pipeline now, run it later | `pipeline create --file` |
| Author + smoke-run in one step (typical first-time flow) | `pipeline save-and-run --file` |
| Re-run an existing pipeline | `pipeline run <pipeline-id>` (no file needed) |

Both `create` and `save-and-run` need `Pipelines.Edit`; `save-and-run` and `run` additionally need `Pipelines.Run` on the active runtime environment.

## Invocation

The file is the same `PipelineDto` shape `pipeline create` consumes — camelCase keys. See [pipeline-dto-guide.md](pipeline-dto-guide.md).

```bash
uip aops pipeline save-and-run --file ./pipeline-<name-kebab>.json --output json
```

Success envelope:

```json
{
  "Result": "Success",
  "Code": "PipelineSavedAndRunStarted",
  "Data": {
    "Pipeline": { "Identifier": "<new-pipeline-id>", "Name": "…", "Branch": "main" },
    "ExecutionId": "<execution-id-or-null>"
  }
}
```

Capture both:

- `Data.Pipeline.Identifier` → future `pipeline run` / `update` / `delete` calls
- `Data.ExecutionId` → `execution logs --follow` to watch

Optional: `--telemetry-flow-id <id>` rides the URL as a correlation query parameter; the body is unchanged. Only pass it when the user supplies one.

## Runs are asynchronous

The service answers `202` with no body. Neither `run` nor `save-and-run` tells you whether the build succeeded — only that it was queued. `run` echoes back just the pipeline id (`Code: "PipelineRunStarted"`, `Data: {PipelineId}`); `save-and-run` additionally lifts the queued execution's id out of the persisted DTO's `latestPipelineExecution` so the caller can chain straight into `execution logs` without re-listing.

Tracking a run to completion is `execution logs --follow`'s job.

## Handling `ExecutionId: null`

When `ExecutionId` is `null`, the run was queued server-side but the response didn't carry the execution row.

Recovery:

```bash
uip aops pipeline executions <new-pipeline-id> --limit 1 --output json
```

Returns `Data[0].ExecutionId` for the freshly-queued run. Note `pipeline executions` takes `--limit` / `--offset` only — `--take` does not exist on this verb.

## Follow the execution to terminal state

```bash
uip aops execution logs <execution-id> --follow --output json
```

`--follow` polls until the execution reaches a terminal state (`Successful`, `Faulted`, `Stopped`), then emits a final summary envelope on stdout carrying the terminal state and line count.

Output routing with `--follow`:

- Log lines stream to **stderr** as they arrive, shaped by `--output` (one `Message` object per line under `--output json`).
- stdout carries only the final envelope.
- The stream is command output, not a diagnostic — it ignores `--log-level` and is not captured by `--log-file`. Redirect stderr to keep it: `2> build.log`.

Flags:

| Flag | Default | Notes |
|---|---|---|
| `--limit <n>` | 200 | Page size for each log fetch |
| `--poll-interval <ms>` | 2000 | Interval between polls when `--follow` is set |
| `--timeout <ms>` | 1800000 (30 min) | Maximum time to follow before giving up |
| `--job-key <key>` | — | Use a JobKey directly, skipping the executionId lookup |

`--follow` requires the `<execution-id>` positional — state polling is executionId-keyed, so `--job-key` alone is rejected. Without `--follow`, the verb drains the current log slice and exits, and `--job-key` alone is enough.

Units always live in the placeholder (`<ms>`) — there is no `--timeout-ms` flag.

## Inspect a single execution

```bash
uip aops execution get <execution-id> --output json
```

Returns the `PipelineExecutionDto` — state, run mode, `JobExecutionIdentifier`, commit info, timing. Reuse `JobExecutionIdentifier` as `--job-key` for `logs` / `details` / `stop` to skip the auto-lookup.

```bash
uip aops execution get <execution-id> --with-arguments --output json
```

`--with-arguments` does one extra round-trip and merges the parsed runtime input arguments into `Data.InputArguments`. Edge cases, none of which fail the verb:

- Runner hasn't picked up the job yet → `InputArguments: null` + a warning
- Job-details API throws → `InputArguments: null` + a warning
- The stored value is malformed JSON → falls back to the raw string, no warning

## Stop a running execution

```bash
uip aops execution stop <execution-id> --wait --output json
```

Idempotent — stopping an already-terminal execution returns the current state without erroring. `--wait` polls until the execution settles to terminal and reports the final state in `Data`. Defaults: `--poll-interval` 2000, `--timeout` 300000 (5 min). Without `--wait`, the verb returns as soon as the stop is queued.

## Not-found detection

`execution get` / `logs` / `details` / `stop` all surface `Execution <id> not found.` with actionable Instructions when the execution id is bogus — the CLI checks the response body rather than trusting a `200`. Re-list with `pipeline executions <pipeline-id>` rather than retrying.

## Full save-and-run + follow chain

```bash
# 1. Save and run, capture the ids
RESULT=$(uip aops pipeline save-and-run --file ./pipeline.json --output json)
PIPELINE_ID=$(echo "$RESULT" | python3 -c "import json,sys;print(json.load(sys.stdin)['Data']['Pipeline']['Identifier'])")
EXECUTION_ID=$(echo "$RESULT" | python3 -c "import json,sys;d=json.load(sys.stdin)['Data']['ExecutionId'];print(d if d else '')")

# 2. Fall back if ExecutionId was null
if [ -z "$EXECUTION_ID" ]; then
  EXECUTION_ID=$(uip aops pipeline executions "$PIPELINE_ID" --limit 1 --output json \
    | python3 -c "import json,sys;print(json.load(sys.stdin)['Data'][0]['ExecutionId'])")
fi

# 3. Follow to terminal state, keeping the streamed lines
uip aops execution logs "$EXECUTION_ID" --follow --output json 2> build.log
```

`--output-filter` is a lighter alternative when only one field is needed — and `save-and-run` has no defaulted `--limit`, so no explicit `--limit` is required:

```bash
uip aops pipeline save-and-run --file ./pipeline.json --output json --output-filter "Data.ExecutionId"
```

The same shortcut on `pipeline executions` DOES need an explicit `--limit`, because that verb's `--limit` has a declared default:

```bash
uip aops pipeline executions "$PIPELINE_ID" --limit 1 --output json --output-filter "Data[0].ExecutionId"
```

## Stop conditions

| Command | `--poll-interval` default | `--timeout` default |
|---|---|---|
| `execution logs --follow` | 2000 | 1800000 (30 min) |
| `execution stop --wait` | 2000 | 300000 (5 min) |
| `connection sync --wait` | 2000 | 300000 (5 min) |

When a follow times out, report the last known state to the user and hand them the `execution get <id>` command — do not silently re-follow.
