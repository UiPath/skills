# SAP Application Scope — no connection configured (RfcConfigurationException, not a BAPI or outage)

Faithful-replay scenario for the `uipath-troubleshoot` skill. Covers the connection-configuration failure of `UiPath.SAP.BAPI.Activities.SapApplicationScope`.

## What this exercises

A `SAP Application Scope` faults while opening the RFC connection because no connection parameters (application/message server) were configured. The job ends Faulted with `SAP.Middleware.Connector.RfcConfigurationException: Not any kind of host is specified` (from `RfcDestination.CheckConfiguration()` via `SapConnectionService.Connect`), before any BAPI or network call. The agent must read the **connection-config signature** as the cause (missing SAP connection parameters) — not blame the BAPI (none ran), a live SAP outage (`RfcCommunicationException`), a logon problem (`RfcLogonException`), or a workflow-logic bug. The fix is to configure the Application/Message Server + client/user/password.

Signature captured **verbatim from a live `uip rpa` run** of a `SapApplicationScope` with empty connection parameters (no SAP system needed — the SAP .NET Connector rejects the config before any network call). Workflow/process names neutralized. Maps to the [sap-connection-failed](../../../../../skills/uipath-troubleshoot/references/activity-packages/sap-bapi-activities/playbooks/sap-connection-failed.md) playbook.

## Mock surface

| Command | Fixture |
|---|---|
| `or folders list` | `or-folders-list.json` |
| `or jobs list --folder-key <Shared> [--state Faulted]` | `or-jobs-list-faulted.json` |
| `or jobs get <key>` | `or-jobs-get.json` (Faulted, RfcConfigurationException: Not any kind of host is specified) |
| `or jobs logs <key> [--level Error]` | `or-jobs-logs.json` |
| `or jobs traces <key>` / `traces spans get --job-key <key>` | empty (no spans emitted) |
| `docsai ask` | passthrough |

No project source is staged — the conclusion is reachable from the job evidence (the config error is in the Info / Error log).

## Success criteria

`skill_triggered` + `llm_judge` (graded against `RESOLUTION.md`, final response only).
