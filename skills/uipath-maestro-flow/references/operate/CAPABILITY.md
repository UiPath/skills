# Operate — Ship, run, and manage deployed flows

Capability index for the lifecycle of a flow as a deployed asset. Operate owns everything that touches the cloud — `solution resources refresh`, Studio Web upload, Orchestrator deploy, `flow debug`, `process run`, `job status/traces`, and `instance` lifecycle (pause, resume, cancel, retry). Requires `uip login`.

> **Where you came from / where to go next.** Operate is downstream of Author (build the flow → ship it) and upstream of Diagnose (run faults → diagnose). Build/edit lives in [author/CAPABILITY.md](../author/CAPABILITY.md); fault triage lives in [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md).
>
> **Inherits universal rules from [SKILL.md](../../SKILL.md)** — `--output json` + prefer `--output-filter` for extraction, no `flow debug` without consent, never invoke other skills automatically, dropdown question pattern, solution layout, **plain-English narration + granular progress list (opt-in — silent by default; engage when the user asks for verbosity)**. The rules below are operate-scoped and apply on top.

## When to use this capability

- Push a flow to Studio Web (`uip solution upload`)
- Deploy a flow to Orchestrator (`uip maestro flow pack` + `uip solution publish`)
- Run a flow end-to-end via `uip maestro flow debug` (cloud round-trip with real side effects)
- Trigger a deployed process via `uip maestro flow process run`
- Check job status or stream traces with `uip maestro flow job status` / `job traces`
- Manage a running instance — pause, resume, cancel, or retry
- Refresh solution resources after binding changes (`uip solution resources refresh`)

## Critical rules

1. **Always run `uip solution resources refresh --solution-folder <SolutionDir>` before `solution upload` or `flow debug`.** Stale resource declarations cause runtime binding failures even when the local `.flow` is correct. The refresh syncs connection and process resource declarations from the project's `bindings_v2.json` files into the solution. `refresh` has no positional solution argument; omit `--solution-folder` only when the current directory is already the solution root.
2. **Default to Studio Web when the user says "publish" without specifier.** "Publish" → `uip solution upload <SolutionDir>`. Only run `uip maestro flow pack` + `uip solution publish` when the user explicitly asks to deploy to Orchestrator. Pass the exact solution root path (the directory containing the `.uipx` file), or `.` when already in that directory; do not pass the solution name while the shell is inside a nested project folder. The Orchestrator path bypasses Studio Web — the user cannot visualize or edit the flow there.
3. **Always include `--folder-key <FOLDER_KEY>` (`-f` shorthand) on `instance` commands.** Without it the command rejects the request before reaching the API. Get the folder key from `uip or folders list --output json` or from the job/process context. See [shared/cli-conventions.md](../shared/cli-conventions.md#6---folder-key-requirement).
4. **Always report Studio Web URL and Instance ID as the first two lines of any debug summary.** Parse `Data.studioWebUrl` and `Data.instanceId` from the JSON output. Use `<not returned by CLI>` if missing — never omit the line. Users need these immediately, not buried below status text.

## Workflow

| Journey | Read |
| --- | --- |
| Publish a flow (Studio Web default, Orchestrator on request) | [ship.md](references/ship.md) |
| Run a flow on demand or check progress | [run.md](references/run.md) |
| Intervene in a running instance | [manage.md](references/manage.md) |

## Common tasks

| I need to... | Read these |
| --- | --- |
| **Publish a flow to Studio Web** | [ship.md — Path 1](references/ship.md#path-1--studio-web-upload-default) |
| **Deploy a flow to Orchestrator** (only if explicitly requested) | [ship.md — Path 2](references/ship.md#path-2--orchestrator-deploy-explicit-only) + [/uipath:uipath-solution](/uipath:uipath-solution) |
| **Sync solution resource declarations** | [ship.md — Pre-flight](references/ship.md#pre-flight) (the `uip solution resources refresh` step) |
| **Debug a flow end-to-end** | [run.md — Debug](references/run.md#debug--controlled-end-to-end-run) |
| **Pass input arguments to `flow debug`** | [run.md — Debug](references/run.md#debug--controlled-end-to-end-run) (the `--inputs` flag) |
| **Bind local files to file-typed inputs** | [run.md — Debug](references/run.md#debug--controlled-end-to-end-run) and [run.md — Process run](references/run.md#process-run--trigger-a-deployed-process) (same `--attachment <variableId>=<localPath>` flag on both, repeatable; `--attachment` overrides `--inputs` on key collisions) |
| **Trigger a deployed process** | [run.md — Process run](references/run.md#process-run--trigger-a-deployed-process) |
| **Check status of a running job** | [run.md — Job inspection](references/run.md#job-inspection--status-and-traces) |
| **Stream verbose execution traces** | [run.md — Job inspection](references/run.md#job-inspection--status-and-traces) (use sparingly — see [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md)) |
| **Pause a running instance** | [manage.md](references/manage.md) |
| **Resume a paused instance** | [manage.md](references/manage.md) |
| **Cancel an instance** | [manage.md](references/manage.md) |
| **Retry a faulted instance** | [manage.md](references/manage.md) (after diagnosing root cause via [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md)) |
| **Look up `solution` / `flow pack` / `flow debug` / `process` / `job` / `instance` CLI syntax** | [shared/cli-commands.md](../shared/cli-commands.md) |
| **My flow run failed** | [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md) |

## Anti-patterns

- **Never run `solution upload` without `solution resources refresh` first.** Stale resource declarations cause runtime binding failures.
- **Never default to Orchestrator deploy when the user said "publish".** "Publish" → Studio Web upload. Confirm explicitly before running `flow pack` + `solution publish`.
- **Never run `flow debug` as a validation step.** Use `uip maestro flow validate` for correctness checking; debug is for end-to-end execution against real systems.
- **Never `retry` a faulted instance without diagnosing the root cause first.** Triage via [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md) — read incidents, runtime variables, and the deployed asset. Then decide whether to retry, cancel, or re-author.
- **Never start diagnosis from `job traces`.** Traces are last-resort verbose output. Begin with incidents — see [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md) for the priority ladder.

## References

### Operate-scoped

- [ship.md](references/ship.md) — Studio Web upload (default) and Orchestrator deploy (explicit)
- [run.md](references/run.md) — debug, process run, job status/traces
- [manage.md](references/manage.md) — instance lifecycle (pause, resume, cancel, retry)

### Cross-capability (shared)

- [shared/cli-commands.md](../shared/cli-commands.md) — flat CLI lookup including `solution upload`, `solution resources refresh`, `flow pack`, `flow debug`, `flow process`, `flow job`, `flow instance`
- [shared/cli-conventions.md](../shared/cli-conventions.md) — login states, FOLDER_KEY, UIPCLI_LOG_LEVEL, JSON output shape
- [shared/variables-and-expressions.md](../shared/variables-and-expressions.md) — `--inputs` JSON shape for `flow debug`

For Orchestrator deployment via `uip solution publish`, see [/uipath:uipath-solution](/uipath:uipath-solution).
