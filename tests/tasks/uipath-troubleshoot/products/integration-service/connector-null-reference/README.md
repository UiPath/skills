# Connector Activity — NullReferenceException (null connector output enumerated)

Faithful-replay scenario for the `uipath-troubleshoot` skill. Covers the
`System.NullReferenceException` case of TROUB-139 (`ConnectorActivity`).

## What this exercises

A `For Each` iterates the output of an Integration Service connector query
operation that returned **null**, throwing `System.NullReferenceException`. The
exception is opaque (no code, no message detail) — the agent must use the stack
frame (`ForEach\`1` specialized on `IntegrationService.Activities.SWEntities.*_executeQuery_List`)
to conclude it is enumerating a null connector result, and recommend a null/empty
guard. The agent must NOT misattribute it to a connection/auth/operation error.

Signature pattern (the `ForEach` over an `SWEntities` connector-output type) was
mined from the failed-job telemetry CSV.

## Mock surface

| Command | Fixture |
|---|---|
| `or folders list` | `or-folders-list.json` |
| `or jobs list --folder-key <Shared> [--state Faulted]` | `or-jobs-list-faulted.json` |
| `or jobs get <key>` | `or-jobs-get.json` (Faulted, NRE at ForEach) |
| `or jobs logs <key> --level Error` | `or-jobs-logs.json` (names the SWEntities ForEach type) |
| `docsai ask` | passthrough |

No project source is staged — the conclusion is reachable from the job evidence
(stack frame identifies the connector-output enumeration).

## Success criteria

`skill_triggered` + `llm_judge` (graded against `RESOLUTION.md`, final response only).
