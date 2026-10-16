# API Workflows — Overview

UiPath **API Workflows** are a Studio Web project type for real-time, system-to-system integration that runs entirely over APIs — no UI automation, no Windows robot, no agent runtime. Workflow logic is a JSON file (CNCF Serverless Workflow DSL 1.0.0 with UiPath activity-type extensions) executed by `@uipath/api-workflow-executor`. Projects are `Type: "Api"`, packaged into a solution, and published to Orchestrator, where a published workflow runs as an **API process** (its executions are Orchestrator jobs).

## What it depends on

- **Integration Service** — Connector and HTTP activities bind named IS connections for auth (OAuth/API-key/PAT). API Workflows do NOT own connections; a broken/expired/mis-scoped IS connection is a leading cause of cloud-run auth failures (**401/403**). (The connection itself surfaces its broken state as `Result: "Failure"` / `not enabled` on `uip is connections ping`, not as the runtime status — see [connection-auth-failure.md](./playbooks/connection-auth-failure.md).)
- **Orchestrator** — package feed, runtime host, trigger surface (HTTP endpoint / schedule / IS event), and the destination for cloud-run logs and traces.
- **Serverless infrastructure** — API Workflows run serverless, so a job that runs as `RuntimeType` Serverless is subject to the Orchestrator serverless limits (15 minutes per job, allocation quota) even though nothing in the workflow file mentions them. Outbound calls leave by one of two routes — serverless robots (an HTTP activity using manual authentication) or Integration Service (an HTTP activity using connector-based authentication, and every Connector activity) — and the two arrive from **different IP ranges**.
- **Solutions** — the packaging/versioning/deploy container (`uip solution pack`/`publish`/`deploy`).
- **Studio Web** — the sole authoring surface; some faults surface only when a workflow is opened/saved in the designer (see the designer-roundtrip playbooks).

## Where the evidence lives (investigation surfaces)

| Stage | Surface | CLI |
|-------|---------|-----|
| Local / pre-publish | Static validation | `uip api-workflow validate <file> --output json` |
| Local / pre-publish | Runtime execution (expression, logic, connection) | `uip api-workflow run <file> --no-auth --output json` |
| Connection health | IS connection state | `uip is connections ping <uuid> --output json` |
| Cloud run | Job status + fault | `uip or jobs get <job-key> --output json` |
| Cloud run | Execution logs, including anything the workflow's **Log Message** activities or a `console.*` in a Script wrote (Info/Warning/Error) | `uip or jobs logs <job-key> --level Error --output json` |
| Cloud run | Execution trace / spans | `uip traces spans get --job-key <job-key> --output json` |
| How it starts | Trigger settings and firing history (always folder-scoped; `--type` is time, queue or api) | `uip or triggers list --type time --folder-path <FOLDER_PATH> --output json`, `uip or triggers history <TRIGGER_KEY> --folder-path <FOLDER_PATH> --output json` |
| Deployment | Pack / publish / deploy errors | `uip solution pack`/`publish`/`deploy` output |

## Fault families

1. **Runtime execution faults** — the executor returns a non-`Successful` status: expression/JS errors, `<name> is not defined`, undefined `$context.outputs.<Activity>`, loop/logic faults. Reproducible locally with `run --no-auth`. (A job may also read as `Faulted` because a `Response` activity has `markJobAsFailed: true` — a deliberate flag, not a thrown activity.)
2. **Connection faults** — a Connector/HTTP activity fails in cloud with an auth error: **401** (`Invalid Organization or User secret, or invalid Element token provided`) from a wrong activity kind, stale connection UUID, or tenant mismatch; **403 Forbidden** from a broken/disabled or under-scoped connection. A missing connection binding fails locally as a 400 validation error before it reaches the proxy.
3. **Designer-roundtrip faults** — the workflow runs locally but breaks after being opened/saved in Studio Web (literal normalization, multi-key Assign collapse, Response object corruption, dropped connector fields).
4. **Packaging / publish / deploy faults** — pack produces a bad artifact, publish rejects the payload, or the project is invisible in Studio Web (wrong project shape).
5. **Nothing started it** — the workflow never ran and no job record exists. The trigger is switched off, points at an old deployment, or is scheduled wrongly; an event trigger's connection is dead; or whatever was meant to call it (an Agent, Maestro, another workflow) never did. Nothing in the workflow file is at fault.
6. **A platform limit cut it off** — the run stopped at a ceiling instead of finishing: a Script's 10-second budget (`Script execution failed timed out`), a loop's `limit` (which stops the loop quietly, logging `reached iteration limit`, without failing the run), the 15-minute serverless job limit, or a quota rejection. `validate` cannot see any of these, and editing the JSON fixes none of them.
7. **The call never arrived** — a request to a firewalled external system is blocked because the target allows the IP range of the *other* route. The connection pings healthy; the request never lands.

## Scope boundary

This product covers **why an API Workflow failed**. For *building/editing* the workflow JSON, and for the exhaustive designer-roundtrip authoring rules, that is the `uipath-api-workflow` skill's domain. For the connection's own auth internals, cross-reference **Integration Service**. For the Orchestrator job/trigger mechanics, cross-reference **Orchestrator**.
