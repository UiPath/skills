---
confidence: medium
---

# API Workflow Run Returns a Non-Successful Status

## Context

What this looks like:
- `uip api-workflow run` (local) or an Orchestrator API-process job (cloud) returns a failure — `Result: "Failure"` with a `Message`/`Instructions`, or job status `Faulted`
- Usually an activity threw during execution and the workflow did not reach its `Response` — but a `Faulted` job with a clean-looking run can also be a deliberate `Response` outcome (see `markJobAsFailed` below)

What can cause it:
- **Expression fault** — invalid `${...}` syntax, a reference to an undefined variable in strict mode, or a loop iterator / catch variable referenced without its `$` prefix (see [expression-reference-error.md](./expression-reference-error.md))
- **Undefined upstream output** — an activity reads `$context.outputs.<Activity>` but the producing activity did not `export` (see [output-undefined.md](./output-undefined.md))
- **JS_Invoke fault** — missing `return`, a runtime error in the script body, or reading context through `arguments[0]` (the runtime passes nothing to the script)
- **Loop fault** — DoWhile condition variable never updated (infinite loop), missing `#Body`, wrong export pattern
- **Deliberate `markJobAsFailed`** — a `Response` activity with `markJobAsFailed: true` reports the Orchestrator job as `Faulted` even though every activity ran and the response body was returned. The run itself did not error — the workflow chose to fail the job (e.g. a business-rule branch). Check the reached `Response` before assuming an activity threw.
- **Connection fault** (cloud only, IntSvc/Http-kind activities) — see [connection-auth-failure.md](./connection-auth-failure.md)

What to look for:
- Whether the fault reproduces locally with `run --no-auth` (structure/expression/logic) or only in cloud (auth/connection/vendor/scope)
- The failing activity's key (`taskName`) in the error — isolates which activity threw

## Investigation

1. Reproduce and read the executor output: `uip api-workflow run <Workflow.json> --no-auth --output json`. Read `Instructions` first — it often names the fix.
2. If it reproduces locally, triage in category order **Structure > Expression > Activity Config > Logic** (see [investigation_guide.md](../investigation_guide.md)). Run `uip api-workflow validate <Workflow.json> --output json` to catch structural/schema faults the run may mask.
3. If it runs clean locally but the cloud job is `Faulted`, pull the job evidence: `uip or jobs get <job-key> --output json`, then `uip or jobs logs <job-key> --output json` and `uip traces spans get --job-key <job-key> --output json`. If the logs show the workflow reached its `Response` with no activity error, check the reached `Response` for `markJobAsFailed: true` — the job status is driven by that flag, not by a thrown activity. Compare a passing run vs. the faulting run to see which branch set it.
4. Reduce to a minimal repro — isolate the failing activity and confirm each upstream activity `export`s its output.

## Resolution

- **If it reproduces locally:** fix the faulting activity per its category (expression / output / loop / JS_Invoke playbook), then re-run AND re-validate until both pass.
- **If it only fails in cloud:** the shape is sound — pursue connection state, tenant/folder scope, or the real vendor response via the job logs/traces (route to [connection-auth-failure.md](./connection-auth-failure.md) for auth-shaped errors).
- **If a `Response` set `markJobAsFailed: true`:** the run is behaving as authored — the job is failed on purpose. Confirm the business rule is correct; if the fail was unintended, fix the branch/condition that reaches that `Response` (author-side, `uipath-api-workflow`), don't chase a runtime error that isn't there.
- **If the executor `Instructions` names a fix:** apply it directly; the executor's guidance is usually exact.
