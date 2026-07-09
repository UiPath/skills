---
confidence: medium
---

# API Workflow Run Returns a Non-Successful Status

## Context

What this looks like:
- `uip api-workflow run` (local) or an Orchestrator API-process job (cloud) returns a failure — `Result: "Failure"` with a `Message`/`Instructions`, or job status `Faulted`
- A task threw during execution; the workflow did not reach its `Response`

What can cause it:
- **Expression fault** — invalid `${...}` syntax, a reference to an undefined variable in strict mode, or a loop iterator / catch variable referenced without its `$` prefix (see [expression-reference-error.md](./expression-reference-error.md))
- **Undefined upstream output** — a task reads `$context.outputs.<X>` but the prior task did not `export` (see [output-undefined.md](./output-undefined.md))
- **JS_Invoke fault** — missing `return`, a runtime error in the script body, or reading context through `arguments[0]` (the runtime passes nothing to the script)
- **Loop fault** — DoWhile condition variable never updated (infinite loop), missing `#Body`, wrong export pattern
- **Connection fault** (cloud only, IntSvc/Http-kind activities) — see [connection-401.md](./connection-401.md)

What to look for:
- Whether the fault reproduces locally with `run --no-auth` (structure/expression/logic) or only in cloud (auth/connection/vendor/scope)
- The failing task's key in the error — isolates which activity threw

## Investigation

1. Reproduce and read the executor output: `uip api-workflow run <Workflow.json> --no-auth --output json`. Read `Instructions` first — it often names the fix.
2. If it reproduces locally, triage in category order **Structure > Expression > Activity Config > Logic** (see [investigation_guide.md](../investigation_guide.md)). Run `uip api-workflow validate <Workflow.json> --output json` to catch structural/schema faults the run may mask.
3. If it runs clean locally but fails in cloud, pull the job evidence: `uip or jobs get <jobId> --output json`, then `uip or jobs logs <jobId> --output json` and `uip or jobs traces <jobId> --output json`.
4. Reduce to a minimal repro — isolate the failing task and confirm each upstream task `export`s its output.

## Resolution

- **If it reproduces locally:** fix the faulting task per its category (expression / output / loop / JS_Invoke playbook), then re-run AND re-validate until both pass.
- **If it only fails in cloud:** the shape is sound — pursue connection state, tenant/folder scope, or the real vendor response via the job logs/traces (route to [connection-401.md](./connection-401.md) for auth-shaped errors).
- **If the executor `Instructions` names a fix:** apply it directly; the executor's guidance is usually exact.
