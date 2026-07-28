# SAP Application Scope — invalid advanced parameter (SapActivityException, before connect)

Faithful-replay scenario for the `uipath-troubleshoot` skill. Covers the invalid-advanced-parameter case of `UiPath.SAP.BAPI.Activities.SapApplicationScope` — a distinct exception class from the no-host case.

## What this exercises

A `SAP Application Scope` has an unsupported RFC key in its Advanced Parameters. The UiPath connection layer parses the advanced parameters and rejects the connection before any network call. The job ends Faulted with `UiPath.SAP.BAPI.Utilities.SapActivityException: Advanced Parameters has invalid parameter BOGUSKEY. Connection cannot be established.` (from `SapConnectionService.OverideWithAdvancedParameters`). The agent must read the **invalid-advanced-parameter signature** as the cause — not blame the BAPI (none ran), a missing host (`RfcConfigurationException`), a SAP outage (`RfcCommunicationException`), logon (`RfcLogonException`), or a workflow bug. The fix is to remove/correct the advanced parameter.

Signature captured **verbatim from a live `uip rpa` run** of a `SapApplicationScope` with `AdvancedParameters="BOGUSKEY=abc"` (no SAP system — the advanced-param check runs before any network call). Workflow/process names neutralized. Maps to the [sap-connection-failed](../../../../../skills/uipath-troubleshoot/references/activity-packages/sap-bapi-activities/playbooks/sap-connection-failed.md) playbook (the `SapActivityException` advanced-parameter branch).

## Mock surface

| Command | Fixture |
|---|---|
| `or folders list` | `or-folders-list.json` |
| `or jobs list --folder-key <Shared> [--state Faulted]` | `or-jobs-list-faulted.json` |
| `or jobs get <key>` | `or-jobs-get.json` (Faulted, SapActivityException: Advanced Parameters has invalid parameter …) |
| `or jobs logs <key> [--level Error]` | `or-jobs-logs.json` |
| `or jobs traces <key>` / `traces spans get --job-key <key>` | empty (no spans emitted) |
| `docsai ask` | passthrough |

No project source is staged — the conclusion is reachable from the job evidence (the config error is in the Info / Error log).

## Success criteria

`skill_triggered` + `llm_judge` (graded against `RESOLUTION.md`, final response only).
