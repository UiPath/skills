# API Workflows — Investigation Guide

Product-specific verification rules. Apply before drawing conclusions, regardless of playbook confidence.

## 1. Reproduce locally before chasing the cloud

Most API Workflow faults are deterministic and reproduce with the local executor. Before reading cloud logs:

```bash
uip api-workflow validate <Workflow.json> --output json   # static: schema + semantic
uip api-workflow run <Workflow.json> --no-auth --output json  # runtime: expression / logic
```

- `validate` reports `Status: Valid` for a workflow whose fault is a **runtime** expression binding (e.g. a loop iterator referenced without its `$` prefix). A `Valid` result does NOT clear the workflow — always attempt a run.
- If `run --no-auth` reproduces the fault, it is a structure/expression/logic fault (not auth or connection). Fix locally; the cloud will inherit the fix.
- If `run --no-auth` succeeds but the cloud run fails, the fault is auth, connection state, real vendor response, trigger payload, or tenant/folder scope — move to the cloud surfaces below.

`--no-auth` skips credential loading. It covers control-flow-only workflows and HTTP Request activities in **manual authentication** (`bodyParameters.authentication: "manual"`, `connectionId: "ImplicitConnection"` — auth details are supplied in the request itself). Anything bound to a real IS connection needs auth at run time even locally: every IntSvc-kind (vendor connector) activity, and an HTTP Request in **connector-based authentication** (`bodyParameters.authentication: "connector"` + `targetConnector` + a real connection UUID in `connectionId`).

## 2. Fix in category order

Triage faults **Structure > Expression > Activity Config > Logic**. A higher-category fix often resolves lower-category symptoms automatically — do not chase a logic symptom before the structure is sound.

## 3. Read `Instructions` first

The executor's failure output carries `Message` + `Instructions`; the `Instructions` field frequently names the fix directly. Read it before forming a hypothesis.

## 4. Confirm the connection actually works — don't trust the listing

For any connection-bound activity (IntSvc kind, or Http kind in connector-based authentication), a connection that appears `Enabled` in `uip is connections list` can still be stale/orphaned. Confirm with a ping before concluding the workflow shape is at fault:

```bash
uip is connections ping <connection-uuid> --output json   # Code: "ConnectionPing" = usable
```

A workflow authored against a non-pinging connection fails in cloud regardless of how correct the JSON is. The filtered `list <connectorKey>` can return a different (broken) UUID than the unfiltered / `--all-folders` listing — check all before deciding a connection doesn't exist.

## 5. Correlate the cloud run to the right job

A published API Workflow runs as an Orchestrator API-process **job**. When investigating a cloud failure, verify you are reading the correct job in the correct folder before interpreting logs:

```bash
uip or jobs get <job-key> --output json                  # status + fault summary
uip or jobs logs <job-key> --output json                 # execution logs
uip traces spans get --job-key <job-key> --output json   # span-level trace
```

Confirm the job's process is the one the user means, and that the folder matches — the same package can be deployed to multiple folders with different connections bound.

## 6. Suspect the designer if "runs locally, breaks after Studio Web"

If the workflow ran under `uip api-workflow run` and only broke after being opened/saved in Studio Web, the on-disk file was rewritten by the designer's normalization passes (literal wrapping, multi-key Assign collapse, Response object corruption, dropped connector fields). Treat the file on disk as authoritative and diff it against the last-known-good version.

## 7. Before blaming the workflow, check that it ran and was allowed to finish

Three kinds of failure leave no trace in the workflow file. `validate` passes, `run --no-auth` reproduces nothing, so an investigation that stays local decides the workflow is healthy and stops. Check all three before you report no fault found:

1. **Did a job exist at all?** If the user says it didn't run, find out whether a job record exists before you go looking for a fault. No job means something failed to start it, not that the workflow is broken — [never-ran-no-job.md](./playbooks/never-ran-no-job.md).
2. **Did the run finish on its own, or get cut off?** A run that stops with nothing to explain it, and that depends on the size of the input, hit a platform limit — a Script's 10-second budget, a loop's `limit`, or the 15-minute serverless ceiling — [platform-limits.md](./playbooks/platform-limits.md).
3. **Did the outbound call reach the target?** A healthy connection plus a call that times out against a firewalled host is a network problem, not an auth one. Which of the two IP ranges applies depends on how the activity authenticates — [outbound-call-blocked.md](./playbooks/outbound-call-blocked.md).

## 8. Read whatever the workflow logged about itself

A `Log Message` activity becomes a `run.script` task carrying `metadata.activityType: "LogMessage"` and a `console.<level>` call. Its output — and any `console.*` inside a Script activity — is collected and written to Orchestrator Logs as Info, Warning or Error:

```bash
uip or jobs logs <JOB_KEY> --level Error --output json
```

Finding none is also worth saying. A workflow with no `Log Message` activities and no `console.*` in its Scripts says nothing about its own progress, so the per-activity output of a local `run` is all you will get. Say that, rather than reporting the logs as empty.
