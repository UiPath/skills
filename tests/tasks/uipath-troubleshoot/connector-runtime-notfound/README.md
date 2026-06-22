# Connector Activity — RuntimeException DAP-RT-1101 (operation NotFound)

Faithful-replay scenario for the `uipath-troubleshoot` skill. Covers the
`RuntimeException` case of TROUB-139 (`ConnectorActivity`).

## What this exercises

A `ConnectorActivity` ("Salesforce: Get Record") resolves its connection fine,
sends the request, and the external service answers **HTTP 404**. The IS runtime
surfaces this as `RuntimeException` with error code **DAP-RT-1101** /
`Status code: NotFound`. The agent must distinguish this **operation-level**
failure (missing record / wrong ID) from a connection-resolution failure
(`DAP-GE-*`), and recommend correcting the referenced record identifier.

Signatures were mined verbatim from the failed-job telemetry CSV.

## Mock surface

| Command | Fixture |
|---|---|
| `or folders list` | `or-folders-list.json` |
| `or jobs get <key>` | `or-jobs-get.json` (Faulted, Info = DAP-RT-1101 NotFound) |
| `or jobs logs <key> --level Error` | `or-jobs-logs.json` |
| `docsai ask` | passthrough |

No project source is staged — the conclusion is reachable from the job evidence
(the failing record ID is in `InputArguments`).

## Success criteria

`skill_triggered` + `llm_judge` (graded against `RESOLUTION.md`, final response only).
