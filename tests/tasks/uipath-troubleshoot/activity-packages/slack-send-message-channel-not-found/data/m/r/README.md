# Slack Send Message — channel_not_found (read the ProviderMessage, not the HTTP 400)

Faithful-replay scenario for the `uipath-troubleshoot` skill. Covers the `UiPath.BAF.Infrastructure.Exceptions.BusinessActivityExecutionException` case of `UiPath.Slack.IntegrationService.Activities.SendMessage`.

## What this exercises

A Slack **Send Message** ("Send Message to Channel") faults *after* its Integration Service connection resolves, because the Slack Web API rejects the call. The job ends Faulted with `BusinessActivityExecutionException` carrying `Error Code: [400]` and the raw Slack `ProviderMessage: {"ok":false,"error":"channel_not_found",...}`. The agent must read the **Slack `error` code** (`channel_not_found`) as the cause — not stop at the generic HTTP 400, and not blame connection resolution (that would be a `System.AggregateException` / `ConnectionException`, a different playbook). The fix is to correct the Channel argument.

Signature captured verbatim from a real Orchestrator job produced by running a Slack `SendMessage` against a non-existent channel on a live Integration Service connection. Maps to the [slack-api-error](../../../../../skills/uipath-troubleshoot/references/activity-packages/slack-activities/playbooks/slack-api-error.md) playbook.

## Mock surface

| Command | Fixture |
|---|---|
| `or folders list` | `or-folders-list.json` |
| `or jobs list --folder-key <Shared> [--state Faulted]` | `or-jobs-list-faulted.json` |
| `or jobs get <key>` | `or-jobs-get.json` (Faulted, BusinessActivityExecutionException + Slack ProviderMessage) |
| `or jobs logs <key> [--level Error]` | `or-jobs-logs.json` |
| `or jobs traces <key>` / `traces spans get --job-key <key>` | empty (no spans emitted) |
| `docsai ask` | passthrough |

No project source is staged — the conclusion is reachable from the job evidence (the Slack error is in the Info / Error log).

## Success criteria

`skill_triggered` + `llm_judge` (graded against `RESOLUTION.md`, final response only).
