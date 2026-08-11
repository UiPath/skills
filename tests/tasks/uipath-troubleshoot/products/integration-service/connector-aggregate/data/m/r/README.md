# Connector Activity — AggregateException (unwrap to inner cause)

Faithful-replay scenario for the `uipath-troubleshoot` skill. Covers the
`System.AggregateException` case of TROUB-139 (`ConnectorActivity`).

## What this exercises

A `ConnectorActivity` ("Salesforce: Create Record") faults with
`System.AggregateException` whose inner exception is a `GeneralException`
**DAP-GE-3000** with detail **Bad Gateway** (a transient 502 during connection
resolution). The agent must **unwrap `InnerExceptions[0]`** — the aggregate is
only the async wrapper — and conclude a transient platform error, recommending a
retry. The agent must NOT treat `AggregateException` itself as the root cause.

Signature mined verbatim from the failed-job telemetry CSV.

## Mock surface

| Command | Fixture |
|---|---|
| `or folders list` | `or-folders-list.json` |
| `or jobs list --folder-key <Shared> [--state Faulted]` | `or-jobs-list-faulted.json` |
| `or jobs get <key>` | `or-jobs-get.json` (Faulted, AggregateException + inner GeneralException) |
| `or jobs logs <key> --level Error` | `or-jobs-logs.json` |
| `docsai ask` | passthrough |

No project source is staged — the conclusion is reachable from the job evidence
(the inner exception is in the Info / log).

## Success criteria

`skill_triggered` + `llm_judge` (graded against `RESOLUTION.md`, final response only).
