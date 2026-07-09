# API Workflows — Overview

UiPath **API Workflows** are a Studio Web project type for real-time, system-to-system integration that runs entirely over APIs — no UI automation, no Windows robot, no agent runtime. Workflow logic is a JSON file (CNCF Serverless Workflow DSL 1.0.0 with UiPath activity-type extensions) executed by `@uipath/api-workflow-executor`. Projects are `Type: "Api"`, packaged into a solution, and published to Orchestrator, where a published workflow runs as an **API process** (its executions are Orchestrator jobs).

## What it depends on

- **Integration Service** — Connector and HTTP activities bind named IS connections for auth (OAuth/API-key/PAT). API Workflows do NOT own connections; a broken/expired/mis-scoped IS connection is a leading cause of cloud-run 401/403/404s.
- **Orchestrator** — package feed, runtime host, trigger surface (HTTP endpoint / schedule / IS event), and the destination for cloud-run logs and traces.
- **Solutions** — the packaging/versioning/deploy container (`uip solution pack`/`publish`/`deploy`).
- **Studio Web** — the sole authoring surface; some faults surface only when a workflow is opened/saved in the designer (see the designer-roundtrip playbooks).

## Where the evidence lives (investigation surfaces)

| Stage | Surface | CLI |
|-------|---------|-----|
| Local / pre-publish | Static validation | `uip api-workflow validate <file> --output json` |
| Local / pre-publish | Runtime execution (expression, logic, connection) | `uip api-workflow run <file> --no-auth --output json` |
| Connection health | IS connection state | `uip is connections ping <uuid> --output json` |
| Cloud run | Job status + fault | `uip or jobs get <jobId> --output json` |
| Cloud run | Execution logs | `uip or jobs logs <jobId> --output json` |
| Cloud run | Execution trace / spans | `uip or jobs traces <jobId> --output json`, `uip traces spans --output json` |
| Deployment | Pack / publish / deploy errors | `uip solution pack`/`publish`/`deploy` output |

## Fault families

1. **Runtime execution faults** — the executor returns a non-`Successful` status: expression/JS errors, `<name> is not defined`, undefined `$context.outputs.<X>`, loop/logic faults. Reproducible locally with `run --no-auth`.
2. **Connection faults** — 401/403/404 from the IS proxy when a Connector/HTTP activity runs in cloud: wrong activity kind for the endpoint, or a connection that is expired/mis-scoped/disabled.
3. **Designer-roundtrip faults** — the workflow runs locally but breaks after being opened/saved in Studio Web (literal normalization, multi-key Assign collapse, Response object corruption, dropped connector fields).
4. **Packaging / publish / deploy faults** — pack produces a bad artifact, publish rejects the payload, or the project is invisible in Studio Web (wrong project shape).

## Scope boundary

This product covers **why an API Workflow failed**. For *building/editing* the workflow JSON, and for the exhaustive designer-roundtrip authoring rules, that is the `uipath-api-workflow` skill's domain. For the connection's own auth internals, cross-reference **Integration Service**. For the Orchestrator job/trigger mechanics, cross-reference **Orchestrator**.
