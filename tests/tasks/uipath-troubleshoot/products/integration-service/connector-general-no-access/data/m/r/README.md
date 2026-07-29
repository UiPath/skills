# Connector Activity — GeneralException DAP-GE-3000 (robot lacks Connections.View)

Faithful-replay scenario for the `uipath-troubleshoot` skill. Covers the
high-volume `GeneralException DAP-GE-3000` case of TROUB-139 / TROUB-141
(`ConnectorActivity` / `ConnectorHttpActivity`).

## What this exercises

A `ConnectorActivity` ("Google Drive: Get File or Folder") faults during
connection resolution because the **executing robot lacks `Connections.View`
permission in the folder where the connection lives** (a different folder than the
one the job runs in). The IS runtime raises `GeneralException` with code
**DAP-GE-3000**. The agent must identify the cross-folder / RBAC cause and
recommend granting `Connections.View` (or moving the connection) — and must NOT
confuse it with a *disabled* connection (`DAP-GE-3005`), an invalid/deleted
connection, an auth failure, or an operation error.

> **Live-anchored:** built from a **real Orchestrator faulted job** on alpha — a
> Google Drive `ConnectorActivity` published to the Shared folder and run by a
> robot, with the connection bound to a different folder the robot can't read.
> The error text, `Connections.View` guidance, and stack frames are verbatim
> (identities scrubbed). Only the job key/folder envelope is reused as-is.

## Mock surface

| Command | Fixture |
|---|---|
| `or folders list` | `or-folders-list.json` |
| `or jobs list --folder-key <Shared> [--state Faulted]` | `or-jobs-list-faulted.json` |
| `or jobs get <key>` | `or-jobs-get.json` (Faulted, real DAP-GE-3000 Connections.View Info) |
| `or jobs logs <key> --level Error` | `or-jobs-logs.json` |
| `or jobs traces <key>` / `traces spans get --job-key <key>` | `traces-empty.json` (both forms; real run had no spans) |
| `docsai ask` | passthrough |

No project source is staged — the conclusion is reachable from the job evidence
(the Info names the connection's folder and the missing permission).

## Success criteria

`skill_triggered` + `llm_judge` (graded against `RESOLUTION.md`, final response only).
