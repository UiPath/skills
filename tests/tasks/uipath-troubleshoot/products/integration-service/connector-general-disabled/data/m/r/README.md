# Connector Activity — GeneralException DAP-GE-3005 (connection disabled)

Faithful-replay scenario for the `uipath-troubleshoot` skill. Covers TROUB-141
(`ConnectorHttpActivity`) and the headline `GeneralException` case of TROUB-139.

## What this exercises

An unattended job faults the moment a `ConnectorHttpActivity` ("Salesforce: HTTP
Request") tries to resolve its Integration Service connection. The connection
exists and is bound, but is in a **Disabled** state, so the IS runtime throws
`GeneralException` with error code **DAP-GE-3005** before any external API call.

The agent must:
1. Trigger the skill, read the faulted job, and key off the verbatim
   `DAP-GE-3005` / "Connection is disabled" signature.
2. Conclude the connection is *disabled* (not missing / no-access / expired) and
   recommend re-enabling (and re-authenticating if it auto-disabled).

Signatures (message text, error code, stack frames) were mined verbatim from the
failed-job telemetry CSV — not invented.

## Mock surface

CLI is mocked via the shared manifest dispatcher (`../_shared/mock_template`):

| Command | Fixture |
|---|---|
| `or folders list` | `or-folders-list.json` |
| `or jobs get <key>` | `or-jobs-get.json` (Faulted, Info = DAP-GE-3005) |
| `or jobs logs <key> --level Error` | `or-jobs-logs.json` |
| `is connections ping <id>` | `is-connections-ping.json` (disabled, exit 1) |
| `is connections list` | `is-connections-list.json` (State: Disabled) |
| `docsai ask` | passthrough |

No project source is staged — the conclusion is reachable from the job evidence
alone; the simulator tells the agent source is unavailable and to proceed.

## Success criteria

`skill_triggered` + `llm_judge` (graded against `RESOLUTION.md`, final response only).
