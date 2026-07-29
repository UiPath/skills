# Terminal Session — Connection Failed (unwrap AggregateException → TerminalConnectionException)

Faithful-replay scenario for the `uipath-troubleshoot` skill. Covers the `System.Exception` / `System.AggregateException` case of `UiPath.Terminal.Activities.TerminalSession`.

## What this exercises

A `TerminalSession` ("Mainframe Session") faults at connection open because the configured host is unreachable. The job ends Faulted with `System.AggregateException` whose inner exception is `UiPath.Terminal.Data.TerminalConnectionException: There was an error connecting to terminal. Error code: UnknownError | ResultCode=UnknownError | ConnectionStatus=Disconnected`. The agent must **unwrap the aggregate** to the inner `TerminalConnectionException`, recognize a **connect failure** (unreachable host / connection settings) — not a workflow-logic bug — and recommend fixing host reachability / connection settings.

Signature captured verbatim from a real Orchestrator job produced by running a `TerminalSession` against an unreachable host (`192.0.2.1`, RFC 5737 TEST-NET-1). Maps to the [terminal-session-connection-failed](../../../../../skills/uipath-troubleshoot/references/activity-packages/terminal-activities/playbooks/terminal-session-connection-failed.md) playbook.

## Mock surface

| Command | Fixture |
|---|---|
| `or folders list` | `or-folders-list.json` |
| `or jobs list --folder-key <Shared> [--state Faulted]` | `or-jobs-list-faulted.json` |
| `or jobs get <key>` | `or-jobs-get.json` (Faulted, AggregateException + inner TerminalConnectionException) |
| `or jobs logs <key> [--level Error]` | `or-jobs-logs.json` |
| `or jobs traces <key>` / `traces spans get --job-key <key>` | empty (connect-time fault emits no spans) |
| `docsai ask` | passthrough |

No project source is staged — the conclusion is reachable from the job evidence (the inner exception is in the Info / Error log).

## Success criteria

`skill_triggered` + `llm_judge` (graded against `RESOLUTION.md`, final response only).
