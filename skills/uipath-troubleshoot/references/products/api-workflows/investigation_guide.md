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

## 7. Before blaming the workflow, confirm it ran and was allowed to finish

Three classes of API Workflow fault have no signature inside the workflow JSON. `validate` clears them and `run --no-auth` reproduces none of them, so an investigation that stays local will conclude the workflow is healthy and stop. Check them explicitly:

1. **Did a job exist at all?** If the user reports "it didn't run", establish whether a job record exists before looking for a fault. No job = an invocation fault, not a workflow fault — see [never-ran-no-job.md](./playbooks/never-ran-no-job.md).
2. **Did the run end on its own logic, or at a ceiling?** A run that stops with no exception accounting for it, and that is input-size-dependent, is a platform limit — the Script activity's 30-second cap, a `Do While` `Limit`, or the serverless 15-minute job ceiling. See [platform-limits.md](./playbooks/platform-limits.md).
3. **Did the outbound call actually reach the target?** A clean connection ping plus a call that times out against a firewalled host is a network-reachability fault, not auth. Which of the two outbound IP ranges applies depends on the activity's authentication mode — see [outbound-call-blocked.md](./playbooks/outbound-call-blocked.md).

## 8. Read the workflow's own Log Message output

`Log Message` writes Info/Warning/Error lines to Orchestrator Logs and is the only native in-workflow observability hook — no Script activity required. Read it with the execution logs:

```bash
uip or jobs logs <job-key> --output json
```

Its absence is also evidence: a workflow with no `Log Message` activities narrates nothing about its own progress, so the per-activity output from a local `run` is the only narrative you will get. Say so rather than reporting the logs as empty.
