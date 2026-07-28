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
